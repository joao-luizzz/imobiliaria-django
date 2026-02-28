from django.shortcuts import redirect
from django.urls import reverse


EXEMPT_PATHS = [
    '/login/',
    '/logout/',
    '/2fa/verificar/',
    '/admin/',
    '/static/',
]


class TwoFactorMiddleware:
    """
    After authentication, intercepts requests from users with 2FA enabled
    and redirects to the verification page until the session key _2fa_done is set.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info
            # Skip exempt paths
            if not any(path.startswith(p) for p in EXEMPT_PATHS):
                if not request.session.get('_2fa_done'):
                    try:
                        profile = request.user.profile
                        if profile.totp_enabled:
                            verify_url = reverse('simulador:verificar_2fa')
                            return redirect(f"{verify_url}?next={request.path}")
                    except Exception:
                        pass

        return self.get_response(request)
