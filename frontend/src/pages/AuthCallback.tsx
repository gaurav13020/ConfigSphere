import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuthStore } from '@/stores/auth';
import { authApi } from '@/services/api';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');

    if (!token) {
      navigate('/auth/error?reason=no_token');
      return;
    }

    setToken(token);

    authApi
      .get('/users/me/', {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(({ data }) => {
        setUser(data);
        navigate('/');
      })
      .catch(() => {
        navigate('/auth/error?reason=profile_fetch_failed');
      });
  }, []);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
      }}
    >
      <CircularProgress sx={{ color: 'white', mb: 3 }} size={48} />
      <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
        Signing you in...
      </Typography>
    </Box>
  );
};

export default AuthCallback;
