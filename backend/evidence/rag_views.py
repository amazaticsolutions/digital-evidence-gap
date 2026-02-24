"""
RAG (Retrieval-Augmented Generation) views for querying evidence.

API Endpoints:
    POST   /api/evidence/rag/ingest/  - Ingest video into RAG system
    POST   /api/evidence/rag/query/   - Query RAG system for relevant frames (stores in chat)
    GET    /api/evidence/rag/stats/   - Get RAG system statistics
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    RAGIngestSerializer,
    RAGQuerySerializer,
    RAGQueryResponseSerializer,
    RAGStatsResponseSerializer,
)

# Import chat and case services for storing conversations
from chat import services as chat_services
from search import services as search_services


class RAGIngestView(APIView):
    """
    Ingest a video into the RAG system for processing.
    
    This endpoint triggers the full RAG pipeline:
    1. Download video from Google Drive
    2. Extract frames at intervals
    3. Generate captions for each frame
    4. Create vector embeddings
    5. Store in MongoDB with vector index
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    @swagger_auto_schema(
        operation_description="Ingest video into RAG system for processing",
        request_body=RAGIngestSerializer,
        responses={
            202: openapi.Response(
                description="Ingestion started",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'video_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'frames_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: 'Validation error',
            401: 'Not authenticated',
            500: 'Ingestion error'
        },
        tags=['RAG']
    )
    def post(self, request):
        """Ingest video into RAG system."""
        serializer = RAGIngestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from multimedia_rag.ingestion import ingest_video
            from multimedia_rag import config
            
            # Validate configuration
            config.validate_config()
            
            video_id = serializer.validated_data.get('video_id')
            gdrive_url = serializer.validated_data.get('gdrive_url')
            gdrive_file_id = serializer.validated_data.get('gdrive_file_id')
            cam_id = serializer.validated_data.get('cam_id', 'unknown')
            gps_lat = serializer.validated_data.get('gps_lat', 0.0)
            gps_lng = serializer.validated_data.get('gps_lng', 0.0)
            
            # Construct Google Drive URL if file_id provided
            if gdrive_file_id and not gdrive_url:
                gdrive_url = f"https://drive.google.com/file/d/{gdrive_file_id}/view"
            
            if not gdrive_url:
                return Response(
                    {"error": "Either gdrive_url or gdrive_file_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Run ingestion pipeline
            frames_processed = ingest_video(
                gdrive_url=gdrive_url,
                cam_id=cam_id,
                gps_lat=gps_lat,
                gps_lng=gps_lng
            )
            
            return Response({
                "success": True,
                "message": "Video ingested successfully",
                "video_id": video_id,
                "frames_processed": frames_processed,
                "gdrive_url": gdrive_url,
            }, status=status.HTTP_202_ACCEPTED)
            
        except ValueError as e:
            return Response(
                {"error": "Configuration error", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ConnectionError as e:
            return Response(
                {"error": "Connection error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except FileNotFoundError as e:
            return Response(
                {"error": "File not found", "details": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Ingestion failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RAGQueryView(APIView):
    """
    Query the RAG system using natural language.
    
    This endpoint executes the complete RAG query pipeline:
    1. Validate query specificity
    2. Vector + keyword search
    3. Temporal expansion (±5 seconds)
    4. LLM scoring and relevance filtering
    5. Metadata enrichment
    6. Timeline generation
    7. Summary generation
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    @swagger_auto_schema(
        operation_description="Query RAG system with natural language",
        request_body=RAGQuerySerializer,
        responses={
            200: RAGQueryResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
            500: 'Query error'
        },
        tags=['RAG']
    )
    def post(self, request):
        """Query evidence using natural language and store in chat history."""
        serializer = RAGQuerySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            case_id = serializer.validated_data['case_id']
            query_text = serializer.validated_data['query']
            top_k = serializer.validated_data.get('top_k', 10)
            enable_reid = serializer.validated_data.get('enable_reid', False)
            filters = serializer.validated_data.get('filters', {})
            
            # Verify case exists and user owns it
            case, case_error = search_services.get_case_by_id(case_id)
            if case_error:
                if "not found" in case_error.lower():
                    return Response(
                        {"error": "Case not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                return Response(
                    {"error": case_error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Check ownership (convert to string for comparison since user_id from MongoDB can be string)
            if str(case['user_id']) != str(request.user.id):
                return Response(
                    {"error": "You don't have permission to query this case"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create chat for the case
            chat, chat_error = chat_services.get_chat_by_case_id(case_id)
            if chat_error:
                return Response(
                    {"error": chat_error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if not chat:
                # Create chat if it doesn't exist
                chat, create_error = chat_services.create_chat(
                    case_id=case_id,
                    user_id=request.user.id,
                    title=case.get('title', f'Case {case_id}')
                )
                if create_error:
                    return Response(
                        {"error": create_error},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Save user's query as a message
            user_message, user_msg_error = chat_services.send_message(
                chat_id=chat['id'],
                user_id=request.user.id,
                content=query_text,
                message_type='user'
            )
            
            if user_msg_error:
                return Response(
                    {"error": f"Failed to save query: {user_msg_error}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Run the RAG query pipeline
            from multimedia_rag.query import run_query, run_reid, get_frame_ids_from_results, format_results_for_display
            
            results = run_query(query_text)
            
            # Run ReID if enabled and we have results
            if enable_reid and results.get('results'):
                frame_ids = get_frame_ids_from_results(results)
                if frame_ids:
                    try:
                        reid_mapping = run_reid(frame_ids)
                        
                        # Add reid_group to results
                        for r in results.get("results", []):
                            r["reid_group"] = reid_mapping.get(r.get("_id"))
                        for r in results.get("timeline", []):
                            r["reid_group"] = reid_mapping.get(r.get("_id"))
                    except Exception as e:
                        # ReID is optional, continue without it
                        results['reid_warning'] = f"ReID failed: {str(e)}"
            
            # Apply additional filters if provided
            if filters:
                video_id = filters.get('video_id')
                cam_id = filters.get('cam_id')
                
                if video_id or cam_id:
                    filtered_results = []
                    for r in results.get('results', []):
                        if video_id and r.get('video_id') != video_id:
                            continue
                        if cam_id and r.get('cam_id') != cam_id:
                            continue
                        filtered_results.append(r)
                    
                    results['results'] = filtered_results
                    results['total_found'] = len(filtered_results)
            
            # Limit results to top_k
            if results.get('results'):
                results['results'] = results['results'][:top_k]
            if results.get('timeline'):
                results['timeline'] = results['timeline'][:top_k]
            
            # Format for API response (remove binary data)
            api_results = format_results_for_display(results, include_images=False)
            
            # Save assistant's response with summary only in content
            # Full results are returned in API response but only summary is saved to chat history
            assistant_message, asst_msg_error = chat_services.send_message(
                chat_id=chat['id'],
                user_id=request.user.id,  # System messages still need a user_id
                content=api_results.get('summary', ''),
                message_type='assistant'
            )
            
            if asst_msg_error:
                # Don't fail the request if we can't save the response
                # Just log the error and continue
                pass
            
            # Add chat info to response
            api_results['chat_id'] = chat['id']
            api_results['user_message_id'] = user_message.get('id')
            api_results['assistant_message_id'] = assistant_message.get('id') if assistant_message else None
            
            return Response(api_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Query failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RAGStatsView(APIView):
    """
    Get RAG system statistics.
    
    Returns information about:
    - Total videos processed
    - Total frames extracted
    - Total embeddings created
    - Index statistics
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get RAG system statistics",
        responses={
            200: RAGStatsResponseSerializer,
            401: 'Not authenticated',
            500: 'Server error'
        },
        tags=['RAG']
    )
    def get(self, request):
        """Get RAG system statistics."""
        try:
            from multimedia_rag.ingestion.mongo_store import get_db
            
            db = get_db()
            
            # Count videos processed
            videos_collection = db['evidence']
            total_videos = videos_collection.count_documents({
                'storage_type': 'gdrive',
                'status': {'$in': ['processed', 'completed']}
            })
            
            # Count frames
            frames_collection = db['frames']
            total_frames = frames_collection.count_documents({})
            
            # Count embeddings (frames with embedding field)
            total_embeddings = frames_collection.count_documents({
                'embedding': {'$exists': True}
            })
            
            # Get index information
            indexes = list(frames_collection.list_indexes())
            vector_index_exists = any(
                'vector' in idx.get('name', '').lower() 
                for idx in indexes
            )
            
            # Calculate approximate index size
            stats = db.command('collstats', 'frames')
            index_size_mb = stats.get('totalIndexSize', 0) / (1024 * 1024)
            
            # Get last updated timestamp
            last_frame = frames_collection.find_one(
                {},
                sort=[('created_at', -1)]
            )
            last_updated = last_frame.get('created_at') if last_frame else None
            
            return Response({
                "total_videos": total_videos,
                "total_frames": total_frames,
                "total_embeddings": total_embeddings,
                "vector_index_exists": vector_index_exists,
                "index_size_mb": round(index_size_mb, 2),
                "last_updated": last_updated.isoformat() if last_updated else None,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve statistics", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
