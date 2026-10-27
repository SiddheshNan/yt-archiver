import { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export function usePathname() {
  const { pathname } = useLocation();

  return useMemo(() => pathname, [pathname]);
}

export function useRouter() {
  const navigate = useNavigate();

  const router = useMemo(
    () => ({
      back: () => navigate(-1),
      forward: () => navigate(1),
      refresh: () => navigate(0),
      push: (href) => navigate(href),
      replace: (href) => navigate(href, { replace: true }),
    }),
    [navigate]
  );

  return router;
}
