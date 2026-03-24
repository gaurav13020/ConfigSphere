import React from 'react';
import { Box } from '@mui/material';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  return (
    <Box sx={{ display: 'flex', height: '100vh', flexDirection: 'column' }}>
      <TopBar />
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            background: 'linear-gradient(135deg, #f5f7ff 0%, #eff2ff 100%)',
            p: 4,
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};
