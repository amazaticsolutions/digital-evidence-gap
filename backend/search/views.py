"""
Search/Case views for case management API.

API Endpoints:
    POST   /api/search/cases/                    - Create a new case
    GET    /api/search/cases/                    - Get all cases for current user (detailed)
    GET    /api/search/cases/summary/            - Get simplified case list (id, title, evidence_count, created_at)
    GET    /api/search/cases/{id}/               - Get case details with evidence
    PATCH  /api/search/cases/{id}/               - Update case
    DELETE /api/search/cases/{id}/               - Delete case
    POST   /api/search/cases/{id}/evidence/      - Add evidence to case
    DELETE /api/search/cases/{id}/evidence/{eid}/ - Remove evidence from case
    POST   /api/search/cases/{id}/assign/        - Assign case to user
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from bson import ObjectId

from .serializers import (
    CreateCaseSerializer,
    CaseResponseSerializer,
    CaseListSerializer,
    CaseDetailSerializer,
    UpdateCaseSerializer,
    AddEvidenceSerializer,
    AssignCaseSerializer,
    CaseSummarySerializer,
    CaseSummaryListSerializer,
)
from . import services


class CaseListCreateView(APIView):
    """
    List all cases for current user or create a new case.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @swagger_auto_schema(
        operation_description="Get all cases for the current user",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (active, completed, archived, pending)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'skip',
                openapi.IN_QUERY,
                description="Number of records to skip (pagination)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Maximum number of records to return",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: CaseListSerializer,
            401: 'Not authenticated',
        },
        tags=['Cases']
    )
    def get(self, request):
        """Get all cases for the current user."""
        status_filter = request.query_params.get('status')
        skip = int(request.query_params.get('skip', 0))
        limit = int(request.query_params.get('limit', 50))
        
        print(services)
        print(request)
        cases, total, error = services.get_user_cases(
            user_id=request.user.id,
            status_filter=status_filter,
            skip=skip,
            limit=limit
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = CaseListSerializer({"cases": cases, "total": total})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Create a new case with optional evidence file uploads",
        manual_parameters=[
            openapi.Parameter(
                'title',
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description='Case title'
            ),
            openapi.Parameter(
                'description',
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description='Case description'
            ),
            openapi.Parameter(
                'evidence_files',
                openapi.IN_FORM,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_FILE),
                required=False,
                description='Evidence files to upload to Google Drive'
            ),
            openapi.Parameter(
                'cam_id',
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description='Camera identifier for evidence files'
            ),
            openapi.Parameter(
                'gps_lat',
                openapi.IN_FORM,
                type=openapi.TYPE_NUMBER,
                required=False,
                description='GPS latitude for evidence files'
            ),
            openapi.Parameter(
                'gps_lng',
                openapi.IN_FORM,
                type=openapi.TYPE_NUMBER,
                required=False,
                description='GPS longitude for evidence files'
            ),
        ],
        responses={
            201: CaseResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
        },
        tags=['Cases']
    )
    def post(self, request):
        """Create a new case with optional evidence file uploads."""
        serializer = CreateCaseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle evidence file uploads if provided
        evidence_ids = []
        if serializer.validated_data.get('evidence_files'):
            try:
                from evidence import services as evidence_services
                
                # Upload files to Google Drive
                upload_result = evidence_services.upload_files_to_gdrive(
                    files=serializer.validated_data['evidence_files'],
                    cam_id=serializer.validated_data.get('cam_id', 'CASE_UPLOAD'),
                    uploaded_by_user_id=str(request.user.id),
                    gps_lat=serializer.validated_data.get('gps_lat'),
                    gps_lng=serializer.validated_data.get('gps_lng'),
                    case_id=None  # Will be set after case creation
                )
                
                # Extract successful evidence IDs
                evidence_ids = upload_result.get('evidence_ids', [])
                
            except Exception as e:
                return Response(
                    {"error": "Failed to upload evidence files", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Create the case
        case, error = services.create_case(
            user_id=request.user.id,
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description'),
            evidence_ids=evidence_ids
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(case, status=status.HTTP_201_CREATED)


class CaseSummaryView(APIView):
    """
    Get a simplified list of all cases for current user.
    
    Returns only essential fields: id, title, evidence_count, created_at
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get simplified case list for the current user (id, title, evidence_count, created_at)",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (active, completed, archived, pending)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'skip',
                openapi.IN_QUERY,
                description="Number of records to skip (pagination)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Maximum number of records to return",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: CaseSummaryListSerializer,
            401: 'Not authenticated',
        },
        tags=['Cases']
    )
    def get(self, request):
        """Get simplified case list for the current user."""
        status_filter = request.query_params.get('status')
        skip = int(request.query_params.get('skip', 0))
        limit = int(request.query_params.get('limit', 50))
        
        cases, total, error = services.get_user_cases(
            user_id=request.user.id,
            status_filter=status_filter,
            skip=skip,
            limit=limit
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Transform cases to include only the required fields
        simplified_cases = []
        for case in cases:
            simplified_cases.append({
                "id": case["id"],
                "title": case["title"],
                "evidence_count": case.get("evidence_count", 0),
                "created_at": case["created_at"]
            })
        
        return Response({
            "cases": simplified_cases,
            "total": total
        }, status=status.HTTP_200_OK)


class CaseDetailView(APIView):
    """
    Get, update, or delete a specific case.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get case details with evidence",
        responses={
            200: CaseDetailSerializer,
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Cases']
    )
    def get(self, request, case_id):
        """Get case details with evidence."""
        case, error = services.get_case_with_evidence(case_id)
        
        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check ownership - compare as strings for consistency
        case_user_id = str(case['user_id']) if case['user_id'] else None
        request_user_id = str(request.user.id) if request.user.id else None
        
        print(f"DEBUG: case_user_id (str) = {case_user_id}")
        print(f"DEBUG: request_user_id (str) = {request_user_id}")
        
        if case_user_id != request_user_id:
            return Response(
                {"error": "You don't have permission to view this case"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(case, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update a case",
        request_body=UpdateCaseSerializer,
        responses={
            200: CaseResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Cases']
    )
    def patch(self, request, case_id):
        """Update a case."""
        serializer = UpdateCaseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check ownership first
        existing_case, error = services.get_case_by_id(case_id)
        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if str(existing_case['user_id']) != str(request.user.id):
            return Response(
                {"error": "You don't have permission to update this case"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        case, error = services.update_case(
            case_id=case_id,
            title=serializer.validated_data.get('title'),
            description=serializer.validated_data.get('description'),
            status=serializer.validated_data.get('status')
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(case, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Delete a case",
        responses={
            204: 'Case deleted successfully',
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Cases']
    )
    def delete(self, request, case_id):
        """Delete a case."""
        # Check ownership first
        existing_case, error = services.get_case_by_id(case_id)
        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if str(existing_case['user_id']) != str(request.user.id):
            return Response(
                {"error": "You don't have permission to delete this case"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, error = services.delete_case(case_id)
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaseEvidenceView(APIView):
    """
    Add or remove evidence from a case.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Add evidence to a case",
        request_body=AddEvidenceSerializer,
        responses={
            200: CaseResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Cases']
    )
    def post(self, request, case_id):
        """Add evidence to a case."""
        serializer = AddEvidenceSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check ownership
        existing_case, error = services.get_case_by_id(case_id)
        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if str(existing_case['user_id']) != str(request.user.id):
            return Response(
                {"error": "You don't have permission to modify this case"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        case, error = services.add_evidence_to_case(
            case_id=case_id,
            evidence_id=serializer.validated_data['evidence_id']
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(case, status=status.HTTP_200_OK)


class CaseEvidenceDeleteView(APIView):
    """
    Remove evidence from a case.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Remove evidence from a case",
        responses={
            200: CaseResponseSerializer,
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Cases']
    )
    def delete(self, request, case_id, evidence_id):
        """Remove evidence from a case."""
        # Check ownership
        existing_case, error = services.get_case_by_id(case_id)
        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if str(existing_case['user_id']) != str(request.user.id):
            return Response(
                {"error": "You don't have permission to modify this case"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        case, error = services.remove_evidence_from_case(
            case_id=case_id,
            evidence_id=evidence_id
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(case, status=status.HTTP_200_OK)


class CaseAssignView(APIView):
    """
    Assign a case to a user.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Assign a case to a user",
        request_body=AssignCaseSerializer,
        responses={
            200: CaseResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Cases']
    )
    def post(self, request, case_id):
        """Assign a case to a user."""
        serializer = AssignCaseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check ownership
        existing_case, error = services.get_case_by_id(case_id)
        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if str(existing_case['user_id']) != str(request.user.id):
            return Response(
                {"error": "You don't have permission to assign this case"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        case, error = services.assign_case_to_user(
            case_id=case_id,
            assigned_to_user_id=serializer.validated_data['user_id']
        )
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(case, status=status.HTTP_200_OK)