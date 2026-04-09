import { Box, Button, Typography, Card } from '@mui/material';

const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:8001/api/v1';

const LoginPage = () => {
  const handleLogin = () => {
    window.location.href = `${AUTH_URL}/oauth/jira/login/`;
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #8b5cf6 100%)',
      }}
    >
      <Card
        sx={{
          p: 6,
          textAlign: 'center',
          maxWidth: 420,
          width: '100%',
          borderRadius: '16px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}
      >
        <Box sx={{ fontSize: '48px', mb: 2 }}>⚙️</Box>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, color: '#1e293b' }}>
          ConfigSphere
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748b', mb: 4 }}>
          Centralized Configuration Management
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={handleLogin}
          fullWidth
          sx={{
            py: 1.5,
            fontSize: '16px',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #4338ca 0%, #4f46e5 100%)',
            },
          }}
        >
          Sign in with Jira
        </Button>
        <Typography variant="caption" sx={{ display: 'block', mt: 3, color: '#94a3b8' }}>
          You will be redirected to your Jira account for authentication
        </Typography>
      </Card>
    </Box>
  );
};

export default LoginPage;
