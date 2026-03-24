import React from 'react';
import { Card, Box, Typography, CircularProgress } from '@mui/material';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  loading?: boolean;
  color?: string;
}

export const StatsCard = ({ title, value, icon, loading, color = '#4f46e5' }: StatsCardProps) => {
  return (
    <Card
      sx={{
        p: 3,
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 10px 40px rgba(79, 70, 229, 0.1)',
          transform: 'translateY(-2px)',
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {title}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5 }}>
            {loading ? (
              <CircularProgress size={24} />
            ) : (
              <Typography variant="h4" sx={{ fontWeight: 800, background: `linear-gradient(135deg, ${color} 0%, #7c3aed 100%)`, backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                {value}
              </Typography>
            )}
          </Box>
        </Box>
        {icon && (
          <Box
            sx={{
              width: 50,
              height: 50,
              borderRadius: '12px',
              background: `${color}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color,
              fontSize: '24px',
            }}
          >
            {icon}
          </Box>
        )}
      </Box>
    </Card>
  );
};
