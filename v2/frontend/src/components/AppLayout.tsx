import { Box } from '@mui/material';

import { AppSidebar } from './AppSidebar';
import { AppTopBar } from './AppTopBar';

export const AppLayout = ({ children }: { children: React.ReactNode }) => (
  <Box sx={{ display: 'flex', minHeight: '100vh' }}>
    <AppSidebar />
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <AppTopBar />
      <Box sx={{ flex: 1, overflow: 'auto', p: { xs: 2, md: 4 } }}>{children}</Box>
    </Box>
  </Box>
);

