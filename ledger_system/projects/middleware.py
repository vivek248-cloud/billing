from django.shortcuts import redirect




class BlockUnauthorizedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = ['/home/', '/admin-login/', '/client/login/']
        path = request.path_info

        if (
            path.startswith('/static/') or
            path.startswith('/media/') or
            path.startswith('/admin/') or
            path.startswith('/projects/') and path.endswith('/download_invoice/') or
            path.startswith('/client/dashboard/') or
            path.startswith('/payment-invoice/') or
            path.startswith('/open-invoice/')  # ✅ Allow open invoice redirect
        ):
            return self.get_response(request)

        if not request.session.get('admin_logged_in') and not request.session.get('user_logged_in'):
            if path not in allowed_paths:
                return redirect('/home/')

        elif path in ['/admin-login/', '/client/login/']:
            return redirect('/billing/')

        return self.get_response(request)
