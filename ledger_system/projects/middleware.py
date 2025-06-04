from django.shortcuts import redirect




class BlockUnauthorizedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = ['/home/', '/admin-login/', '/client/login/']
        path = request.path_info  # better than request.path for middleware
        
        # Bypass static/media files and admin
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/admin/'):
            return self.get_response(request)

        # Allow invoice download for clients
        if path.startswith('/projects/') and path.endswith('/download_invoice/'):
            return self.get_response(request)
        

        # Allow payment invoice for clients
        if path.startswith('/client/dashboard/'):
            return self.get_response(request)

        if path.startswith('/payment-invoice/'):
            return self.get_response(request)
        # Admin not logged in
        if not request.session.get('admin_logged_in') and not request.session.get('user_logged_in'):
            if path not in allowed_paths:
                return redirect('/home/')

        # Prevent login pages after logged in
        elif path in ['/admin-login/', '/client/login/']:
            return redirect('/billing/')

        return self.get_response(request)
