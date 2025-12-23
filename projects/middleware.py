from django.shortcuts import redirect









# class BlockUnauthorizedMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         path = request.path_info

#         # ✅ Allow these paths even if not logged in
#         always_allowed_paths = [
#             '/home/',
#             '/admin-login/',
#             '/client/login/',
#             '/sitemap.xml',  # ✅ This line is critical
#         ]

#         # ✅ Allow static and public paths
#         if (
#             path.startswith('/static/') or
#             path.startswith('/media/') or
#             path.startswith('/admin/') or
#             path.startswith('/projects/') and path.endswith('/download_invoice/') or
#             path.startswith('/client/dashboard/') or
#             path.startswith('/payment-invoice/') or
#             path.startswith('/open-invoice/') or
#             path in always_allowed_paths
#         ):
#             return self.get_response(request)

#         # ✅ Redirect unauthenticated users
#         if not request.session.get('admin_logged_in') and not request.session.get('user_logged_in'):
#             return redirect('/home/')

#         # ✅ Redirect logged-in users away from login pages
#         if path in ['/admin-login/', '/client/login/']:
#             return redirect('/billing/')

#         return self.get_response(request)




from django.http import HttpResponseBadRequest

class BlockUnauthorizedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            path = request.path_info

            always_allowed_paths = [
                '/home/',
                '/admin-login/',
                '/client/login/',
                '/session-expired/',
                '/sitemap.xml',
            ]


            # ✅ Allow Google Search Console verification files
            if path.startswith('/google') and path.endswith('.html'):
                return self.get_response(request)

            # ✅ Allow static/media/public routes
            if (
                path.startswith('/static/') or
                path.startswith('/media/') or
                (path.startswith('/projects/') and path.endswith('/download_invoice/')) or
                path.startswith('/client/dashboard/') or
                path.startswith('/payment-invoice/') or
                path.startswith('/open-invoice/') or
                path in always_allowed_paths
            ):
                return self.get_response(request)

            # ✅ If session expired or invalid, flush it
            if not request.session.session_key:
                request.session.flush()
                return redirect('session_expired')

            # ✅ Redirect unauthenticated users
            if not request.session.get('admin_logged_in') and not request.session.get('user_logged_in'):
                request.session.flush()
                return redirect('session_expired')


            # ✅ Prevent logged-in users from accessing login pages again
            if path in ['/admin-login/', '/client/login/']:
                return redirect('/billing/')

            return self.get_response(request)

        except Exception as e:
            print("⚠️ Middleware error:", e)
            request.session.flush()
            return redirect('session_expired')