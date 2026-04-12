import {
  AccountTree,
  AdminPanelSettings,
  Approval,
  Dashboard,
  Replay,
} from '@mui/icons-material';
import { Box, Divider, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

const menuItems = [
  { label: 'Dashboard', icon: Dashboard, path: '/' },
  { label: 'Admin & Access', icon: AdminPanelSettings, path: '/admin' },
  { label: 'Services & Tree', icon: AccountTree, path: '/services' },
  { label: 'Change Requests', icon: Approval, path: '/requests' },
  { label: 'Rollbacks', icon: Replay, path: '/rollbacks' },
];

export const AppSidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 288,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 288,
          borderRight: '1px solid rgba(91, 77, 245, 0.08)',
          background: 'linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,255,0.98) 100%)',
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Typography variant="overline" sx={{ color: '#5b4df5', fontWeight: 800, letterSpacing: '0.22em' }}>
          ConfigSphere V2
        </Typography>
        <Typography variant="h6" sx={{ mt: 1 }}>
          Governed Config Control
        </Typography>
      </Box>
      <Divider />
      <List sx={{ p: 2 }}>
        {menuItems.map((item) => {
          const active = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <ListItem disablePadding key={item.path} sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 3,
                  px: 2,
                  py: 1.3,
                  background: active ? 'linear-gradient(135deg, #5b4df5 0%, #7467ff 100%)' : 'transparent',
                  color: active ? 'white' : '#475569',
                  '&:hover': {
                    background: active ? 'linear-gradient(135deg, #5b4df5 0%, #7467ff 100%)' : 'rgba(91,77,245,0.06)',
                  },
                }}
              >
                <ListItemIcon sx={{ color: active ? 'white' : '#64748b', minWidth: 42 }}>
                  <Icon />
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ fontWeight: active ? 700 : 600 }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Drawer>
  );
};
