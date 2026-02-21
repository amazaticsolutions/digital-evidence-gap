"""
Search/Case serializers for case management API.

This module defines request/response serializers for:
- Case creation
- Case listing
- Case details with evidence count
"""

from rest_framework import serializers


class CreateCaseSerializer(serializers.Serializer):
    """
    Serializer for creating a new case.
    
    Request fields:
        title: Case title (required)
        description: Case description (optional)
        evidence_files: List of evidence files to upload to Google Drive (optional)
        cam_id: Camera identifier for evidence files (required if files provided)
        gps_lat: GPS latitude for evidence files (optional)
        gps_lng: GPS longitude for evidence files (optional)
    """
    title = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Case title"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Case description"
    )
    evidence_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        default=list,
        help_text="List of evidence files to upload to Google Drive"
    )
    cam_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100,
        help_text="Camera identifier for evidence files"
    )
    gps_lat = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="GPS latitude for evidence files"
    )
    gps_lng = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="GPS longitude for evidence files"
    )


class CaseResponseSerializer(serializers.Serializer):
    """
    Serializer for case response data.
    """
    id = serializers.CharField(help_text="Case ID")
    case_id = serializers.CharField(allow_null=True, help_text="Case reference ID")
    title = serializers.CharField(help_text="Case title")
    description = serializers.CharField(allow_null=True, help_text="Case description")
    user_id = serializers.IntegerField(help_text="ID of user who created the case")
    assigned_to_user_id = serializers.IntegerField(
        allow_null=True,
        help_text="ID of assigned user"
    )
    assigned_at = serializers.DateTimeField(
        allow_null=True,
        help_text="When case was assigned"
    )
    evidence_count = serializers.IntegerField(help_text="Number of attached evidence")
    evidence_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of evidence IDs"
    )
    status = serializers.CharField(help_text="Case status")
    created_at = serializers.DateTimeField(help_text="Creation date and time")
    updated_at = serializers.DateTimeField(help_text="Last update date and time")


class CaseListSerializer(serializers.Serializer):
    """
    Serializer for case list response.
    """
    cases = CaseResponseSerializer(many=True)
    total = serializers.IntegerField(help_text="Total number of cases")


class CaseDetailSerializer(CaseResponseSerializer):
    """
    Serializer for case detail with evidence information.
    """
    evidence = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="List of evidence details"
    )


class UpdateCaseSerializer(serializers.Serializer):
    """
    Serializer for updating a case.
    """
    title = serializers.CharField(
        required=False,
        max_length=255,
        help_text="Case title"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Case description"
    )
    status = serializers.ChoiceField(
        choices=['active', 'completed', 'archived', 'pending'],
        required=False,
        help_text="Case status"
    )


class AddEvidenceSerializer(serializers.Serializer):
    """
    Serializer for adding evidence to a case.
    """
    evidence_id = serializers.CharField(
        required=True,
        help_text="Evidence ID to add"
    )


class AssignCaseSerializer(serializers.Serializer):
    """
    Serializer for assigning a case to a user.
    """
    user_id = serializers.IntegerField(
        required=True,
        help_text="User ID to assign the case to"
    )


class CaseSummarySerializer(serializers.Serializer):
    """
    Simplified serializer for case summary - shows only essential fields.
    
    Response fields:
        id: Case ID
        title: Case title
        evidence_count: Number of attached evidence
        created_at: Creation date and time
    """
    id = serializers.CharField(help_text="Case ID")
    title = serializers.CharField(help_text="Case title")
    evidence_count = serializers.IntegerField(help_text="Number of attached evidence")
    created_at = serializers.DateTimeField(help_text="Creation date and time")


class CaseSummaryListSerializer(serializers.Serializer):
    """
    Serializer for simplified case list response.
    """
    cases = CaseSummarySerializer(many=True)
    total = serializers.IntegerField(help_text="Total number of cases")