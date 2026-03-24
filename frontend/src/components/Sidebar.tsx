import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Box, Typography, Divider } from '@mui/material';
import { Dashboard, Schema, Settings, History, VisibilityOff, AssignmentInd } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';

const MENU_ITEMS = [
  { label: 'Dashboard', path: '/', icon: Dashboard },
  { label: 'Schemas', path: '/schemas', icon: Schema },
  { label: 'Config Items', path: '/config-items', icon: Settings },
  { label: 'Config Versions', path: '/versions', icon: AssignmentInd },
  { label: 'Resolver', path: '/resolver', icon: VisibilityOff },
  { label: 'Audit Trail', path: '/audit', icon: History },
];

export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 280,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 280,
          boxSizing: 'border-box',
          background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
          borderRight: '1px solid #e2e8f0',
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#4f46e5', fontSize: '12px', letterSpacing: '1px', textTransform: 'uppercase' }}>
          Menu
        </Typography>
      </Box>
      
      <Divider />

      <List sx={{ px: 1 }}>
        {MENU_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: '8px',
                  mx: 1,
                  background: isActive ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' : 'transparent',
                  color: isActive ? 'white' : '#64748b',
                  '&:hover': {
                    background: isActive ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' : '#f1f5f9',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: isActive ? 'white' : '#64748b',
                  }}
                >
                  <Icon />
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  sx={{
                    '& .MuiListItemText-primary': {
                      fontWeight: isActive ? 600 : 500,
                      fontSize: '0.95rem',
                    },
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ position: 'absolute', bottom: 20, left: 0, right: 0, px: 2 }}>
        <Box sx={{ p: 2, background: '#f0f4ff', borderRadius: '8px', textAlign: 'center' }}>
          <Typography variant="caption" sx={{ color: '#4f46e5', fontWeight: 600 }}>
            v1.0.0
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};
