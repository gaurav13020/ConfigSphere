import { Logout, PersonOutline } from '@mui/icons-material';
import { AppBar, Avatar, Box, Chip, IconButton, Toolbar, Tooltip, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { useAuthStore } from '@/stores/auth';

export const AppTopBar = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        background: 'linear-gradient(135deg, rgba(91,77,245,0.98) 0%, rgba(110,95,255,0.98) 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.12)',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Configuration Governance Console
          </Typography>
          <Typography variant="caption" sx={{ opacity: 0.85 }}>
            Precomputed config delivery with approvals, reviews, and rollback
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Chip
            icon={<PersonOutline sx={{ color: 'inherit !important' }} />}
            label={user?.displayName || 'Developer'}
            sx={{
              color: 'white',
              bgcolor: 'rgba(255,255,255,0.12)',
              borderRadius: 99,
            }}
          />
          <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.18)' }}>{user?.displayName?.[0] || 'D'}</Avatar>
          <Tooltip title="Logout">
            <IconButton
              onClick={() => {
                logout();
                navigate('/login');
              }}
              color="inherit"
            >
              <Logout />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

