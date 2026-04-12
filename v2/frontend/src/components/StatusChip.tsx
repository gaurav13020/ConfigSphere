import { Chip } from '@mui/material';

const COLORS: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
  DRAFT: 'default',
  SUBMITTED: 'info',
  IN_REVIEW: 'info',
  CHANGES_REQUESTED: 'warning',
  APPROVED: 'success',
  REJECTED: 'error',
  CONFLICTED: 'error',
  IMPLEMENTING: 'primary',
  IMPLEMENTED: 'success',
  FAILED: 'error',
  REQUESTED: 'warning',
  ROLLED_BACK: 'success',
};

export const StatusChip = ({ value }: { value: string }) => (
  <Chip
    size="small"
    label={value.split('_').join(' ')}
    color={COLORS[value] || 'default'}
    variant={value === 'DRAFT' ? 'outlined' : 'filled'}
    sx={{ fontWeight: 700 }}
  />
);
