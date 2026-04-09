import { Box, Button, Card, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const AuthError = () => {
  const navigate = useNavigate();
  const params = new URLSearchParams(window.location.search);
  const reason = params.get('reason') || 'unknown';

  const messages: Record<string, string> = {
    no_token: 'No authentication token was received. Please try signing in again.',
    profile_fetch_failed: 'Could not fetch your profile. Please try signing in again.',
    unknown: 'An unknown authentication error occurred.',
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
      }}
    >
      <Card sx={{ p: 6, textAlign: 'center', maxWidth: 420, borderRadius: '16px' }}>
        <Box sx={{ fontSize: '48px', mb: 2 }}>⚠️</Box>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#1e293b' }}>
          Authentication Error
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748b', mb: 4 }}>
          {messages[reason] || messages.unknown}
        </Typography>
        <Button
          variant="contained"
          onClick={() => navigate('/login')}
          sx={{
            background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
          }}
        >
          Back to Login
        </Button>
      </Card>
    </Box>
  );
};

export default AuthError;
