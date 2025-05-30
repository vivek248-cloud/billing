from django.shortcuts import redirect


# class BlockUnauthorizedMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Public routes
#         allowed_paths = ['/home/', '/admin-login/', '/client/login/', '/projects/<int:project_id>/download_invoice/']

#         path = request.path

#         # Not logged in
#         if not request.session.get('admin_logged_in') and not request.session.get('user_logged_in'):
#             if path not in allowed_paths:
#                 return redirect('/home/')

#         # Logged in: prevent access to login pages
#         elif path in ['/admin-login/', '/client/login/']:
#             return redirect('/billing/')  # Redirect to billing or dashboard

#         return self.get_response(request)

class BlockUnauthorizedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Public routes without params
        allowed_paths = ['/home/', '/admin-login/', '/client/login/']

        path = request.path

        # Allow invoice download URLs regardless of project_id
        if path.startswith('/projects/') and path.endswith('/download_invoice/'):
            return self.get_response(request)

        # Not logged in
        if not request.session.get('admin_logged_in') and not request.session.get('user_logged_in'):
            if path not in allowed_paths:
                return redirect('/home/')

        # Logged in: prevent access to login pages
        elif path in ['/admin-login/', '/client/login/']:
            return redirect('/billing/')  # Redirect to billing or dashboard

        return self.get_response(request)
