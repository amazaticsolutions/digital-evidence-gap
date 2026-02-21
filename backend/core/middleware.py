"""
Custom middleware for the digital_evidence_gap project.
"""
import logging
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log requests and responses."""
    
    def process_request(self, request):
        request.start_time = time.time()
        logger.info(f"Request: {request.method} {request.path}")
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"Response: {request.method} {request.path} "
                f"[{response.status_code}] {duration:.3f}s"
            )
        return response


class ExceptionHandlingMiddleware(MiddlewareMixin):
    """Middleware to handle exceptions globally."""
    
    def process_exception(self, request, exception):
        logger.error(f"Unhandled exception: {str(exception)}", exc_info=True)
        
        return JsonResponse(
            {
                'error': 'Internal server error',
                'message': 'Something went wrong. Please try again later.',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )