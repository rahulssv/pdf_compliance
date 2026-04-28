"""
Comprehensive API Request/Response Logging Middleware
Captures all incoming HTTP requests and outgoing API calls with full details
"""
import logging
import time
import json
from functools import wraps
from flask import request, g
from typing import Any, Dict, Optional
import traceback

logger = logging.getLogger(__name__)


class APILogger:
    """Middleware for logging all API requests and responses"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        logger.info("✅ API Logger middleware initialized")
    
    @staticmethod
    def before_request():
        """Log incoming request details"""
        from src.config import Config
        
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}"
        
        # Only log detailed info if verbose logging is enabled
        if not Config.ENABLE_VERBOSE_LOGGING:
            return
        
        # Prepare request details
        request_details = {
            "request_id": g.request_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": request.method,
            "url": request.url,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        }
        
        # Log headers (excluding sensitive ones)
        headers = dict(request.headers)
        sensitive_headers = ["Authorization", "X-Api-Key", "Cookie"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "***REDACTED***"
        request_details["headers"] = headers
        
        # Log query parameters
        if request.args:
            request_details["query_params"] = dict(request.args)
        
        # Log request body for POST/PUT/PATCH (with size limit)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    # For JSON, parse and log
                    if request.content_length and request.content_length < 10000:  # 10KB limit
                        request_details["body"] = request.get_json(silent=True)
                    else:
                        request_details["body"] = f"<Large payload: {request.content_length} bytes>"
                elif "multipart/form-data" in content_type:
                    # For file uploads, log metadata only
                    files_info = {}
                    for key, file in request.files.items():
                        files_info[key] = {
                            "filename": file.filename,
                            "content_type": file.content_type,
                        }
                    request_details["files"] = files_info
                    if request.form:
                        request_details["form_data"] = dict(request.form)
                else:
                    request_details["body"] = f"<{content_type}>"
            except Exception as e:
                request_details["body_error"] = str(e)
        
        # Log the incoming request
        logger.info(f"📥 INCOMING REQUEST: {json.dumps(request_details, indent=2, default=str)}")
    
    @staticmethod
    def after_request(response):
        """Log outgoing response details"""
        from src.config import Config
        
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            
            # Only log detailed info if verbose logging is enabled
            if not Config.ENABLE_VERBOSE_LOGGING:
                return response
            
            response_details = {
                "request_id": getattr(g, "request_id", "unknown"),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "status": response.status,
                "duration_ms": round(duration * 1000, 2),
                "content_type": response.content_type,
                "content_length": response.content_length,
            }
            
            # Log response headers (excluding sensitive ones)
            headers = dict(response.headers)
            sensitive_headers = ["Set-Cookie"]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "***REDACTED***"
            response_details["headers"] = headers
            
            # Log response body for non-binary responses (with size limit)
            if response.content_type and "application/json" in response.content_type:
                try:
                    if response.content_length and response.content_length < 10000:  # 10KB limit
                        response_details["body"] = response.get_json(silent=True)
                    else:
                        response_details["body"] = f"<Large response: {response.content_length} bytes>"
                except Exception:
                    pass
            
            # Color code based on status
            if response.status_code < 300:
                log_level = logging.INFO
                emoji = "✅"
            elif response.status_code < 400:
                log_level = logging.INFO
                emoji = "↪️"
            elif response.status_code < 500:
                log_level = logging.WARNING
                emoji = "⚠️"
            else:
                log_level = logging.ERROR
                emoji = "❌"
            
            logger.log(log_level, f"{emoji} OUTGOING RESPONSE: {json.dumps(response_details, indent=2, default=str)}")
        
        return response
    
    @staticmethod
    def teardown_request(exception=None):
        """Log any exceptions that occurred during request processing"""
        if exception:
            error_details = {
                "request_id": getattr(g, "request_id", "unknown"),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "method": request.method,
                "path": request.path,
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc(),
            }
            logger.error(f"💥 REQUEST EXCEPTION: {json.dumps(error_details, indent=2, default=str)}")


def log_external_api_call(func):
    """
    Decorator to log external API calls (e.g., Gemini API)
    Use this to wrap functions that make HTTP requests to external services
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        call_id = f"{int(time.time() * 1000)}"
        start_time = time.time()
        
        # Log the outgoing API call
        call_details = {
            "call_id": call_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "function": func.__name__,
            "module": func.__module__,
        }
        
        # Try to extract API details from kwargs
        if "url" in kwargs:
            call_details["url"] = kwargs["url"]
        if "method" in kwargs:
            call_details["method"] = kwargs["method"]
        if "headers" in kwargs:
            headers = dict(kwargs["headers"])
            # Redact sensitive headers
            for key in ["Authorization", "X-Api-Key", "Api-Key"]:
                if key in headers:
                    headers[key] = "***REDACTED***"
            call_details["headers"] = headers
        if "params" in kwargs:
            call_details["params"] = kwargs["params"]
        if "json" in kwargs:
            call_details["payload"] = kwargs["json"]
        
        logger.info(f"🌐 EXTERNAL API CALL: {json.dumps(call_details, indent=2, default=str)}")
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log the response
            duration = time.time() - start_time
            response_details = {
                "call_id": call_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "function": func.__name__,
                "duration_ms": round(duration * 1000, 2),
                "success": True,
            }
            
            # Try to extract response details
            if hasattr(result, "status_code"):
                response_details["status_code"] = result.status_code
            if hasattr(result, "headers"):
                response_details["response_headers"] = dict(result.headers)
            
            logger.info(f"✅ EXTERNAL API RESPONSE: {json.dumps(response_details, indent=2, default=str)}")
            return result
            
        except Exception as e:
            # Log the error
            duration = time.time() - start_time
            error_details = {
                "call_id": call_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "function": func.__name__,
                "duration_ms": round(duration * 1000, 2),
                "success": False,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            }
            logger.error(f"❌ EXTERNAL API ERROR: {json.dumps(error_details, indent=2, default=str)}")
            raise
    
    return wrapper

