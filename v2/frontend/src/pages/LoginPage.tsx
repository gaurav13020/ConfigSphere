import { Key, Login, PersonAdd } from '@mui/icons-material';
import { Box, Button, Card, Stack, TextField, Typography } from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { authLinks } from '@/services/api';
import { useAuthStore } from '@/stores/auth';

const LoginPage = () => {
  const navigate = useNavigate();
  const loginDev = useAuthStore((state) => state.loginDev);
  const [email, setEmail] = useState('dev-author@example.com');
  const [displayName, setDisplayName] = useState('Dev Author');

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        px: 2,
        background:
          'radial-gradient(circle at top, rgba(124,58,237,0.22), transparent 30%), linear-gradient(135deg, #5b4df5 0%, #6d5fff 35%, #8b5cf6 100%)',
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 520, p: { xs: 3, md: 5 }, borderRadius: 6 }}>
        <Typography variant="overline" sx={{ color: '#5b4df5', fontWeight: 800, letterSpacing: '0.22em' }}>
          ConfigSphere V2
        </Typography>
        <Typography variant="h3" sx={{ mt: 1 }}>
          Govern your config safely
        </Typography>
        <Typography sx={{ mt: 1.5, color: '#64748b', mb: 4 }}>
          Review, approve, implement, and rollback hierarchical configuration changes without exposing clients to partial state.
        </Typography>

        <Stack spacing={2.5}>
          <TextField label="Email" value={email} onChange={(event) => setEmail(event.target.value)} fullWidth />
          <TextField label="Display name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} fullWidth />

          <Button
            variant="contained"
            size="large"
            startIcon={<Login />}
            onClick={() => {
              loginDev(email, displayName);
              navigate('/');
            }}
            sx={{ py: 1.5, background: 'linear-gradient(135deg, #5b4df5 0%, #7467ff 100%)' }}
          >
            Continue in Dev Mode
          </Button>

          <Button variant="outlined" size="large" startIcon={<Key />} href={authLinks.login}>
            Sign in with Keycloak
          </Button>
          <Button variant="text" size="large" startIcon={<PersonAdd />} href={authLinks.signup}>
            Create account
          </Button>
        </Stack>
      </Card>
    </Box>
  );
};

export default LoginPage;

