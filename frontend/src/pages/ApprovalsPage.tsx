import { useEffect, useState } from 'react';
import {
  Box,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { CheckCircle, Cancel, OpenInNew } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { apiClient } from '@/services/api';
import { useAuthStore, hasRole } from '@/stores/auth';
import { ApprovalRequest } from '@/types';

const STATUS_COLORS: Record<string, 'warning' | 'success' | 'error'> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'error',
};

const ApprovalsPage = () => {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewDialog, setReviewDialog] = useState<{
    open: boolean;
    approval: ApprovalRequest | null;
    action: 'approve' | 'reject';
  }>({ open: false, approval: null, action: 'approve' });
  const [comment, setComment] = useState('');
  const { user } = useAuthStore();

  useEffect(() => {
    fetchApprovals();
  }, []);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      setError(null);
      // Use audit events to find versions with approvals
      const res = await apiClient.getAuditEvents({ event_type: 'approval_submitted' });
      // For now, we'll show what we can from the approval endpoints
      // This is a placeholder — the real list endpoint would be on the backend
      setApprovals([]);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch approvals');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = (approval: ApprovalRequest, action: 'approve' | 'reject') => {
    setReviewDialog({ open: true, approval, action });
    setComment('');
  };

  const handleSubmitReview = async () => {
    if (!reviewDialog.approval) return;
    try {
      setLoading(true);
      if (reviewDialog.action === 'approve') {
        await apiClient.approveRequest(reviewDialog.approval.id, comment);
      } else {
        await apiClient.rejectRequest(reviewDialog.approval.id, comment);
      }
      setReviewDialog({ open: false, approval: null, action: 'approve' });
      fetchApprovals();
    } catch (err: any) {
      setError(err.response?.data?.error || `Failed to ${reviewDialog.action} request`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Box sx={{ fontSize: '28px' }}>✅</Box>
              <Box>
                <Box sx={{ fontSize: '24px', fontWeight: 800 }}>Approvals</Box>
                <Box sx={{ fontSize: '14px', color: '#64748b' }}>
                  Review and manage configuration change approvals
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Card
          sx={{
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            border: '1px solid #e2e8f0',
          }}
        >
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : approvals.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center', color: '#94a3b8' }}>
              <Box sx={{ fontSize: '48px', mb: 2 }}>📋</Box>
              <Box>No approval requests found.</Box>
              <Typography variant="body2" sx={{ mt: 1, color: '#94a3b8' }}>
                When operators submit config versions for approval, they will appear here.
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: '#f8fafc' }}>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Version ID</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Jira Ticket</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Submitted By</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Submitted At</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }} align="right">
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {approvals.map((approval) => (
                    <TableRow
                      key={approval.id}
                      sx={{
                        '&:hover': { background: '#f8fafc' },
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>#{approval.config_version}</TableCell>
                      <TableCell>
                        {approval.jira_issue_url ? (
                          <Button
                            size="small"
                            href={approval.jira_issue_url}
                            target="_blank"
                            startIcon={<OpenInNew />}
                            sx={{ textTransform: 'none' }}
                          >
                            {approval.jira_issue_key}
                          </Button>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>{approval.submitted_by}</TableCell>
                      <TableCell>
                        <Chip
                          label={approval.status.toUpperCase()}
                          color={STATUS_COLORS[approval.status] || 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#64748b', fontSize: '0.85rem' }}>
                        {new Date(approval.submitted_at).toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        {approval.status === 'pending' && hasRole(user, 'approver') && (
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                            <Button
                              size="small"
                              variant="outlined"
                              color="success"
                              startIcon={<CheckCircle />}
                              onClick={() => handleReview(approval, 'approve')}
                              sx={{ textTransform: 'none' }}
                            >
                              Approve
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              color="error"
                              startIcon={<Cancel />}
                              onClick={() => handleReview(approval, 'reject')}
                              sx={{ textTransform: 'none' }}
                            >
                              Reject
                            </Button>
                          </Box>
                        )}
                        {approval.status !== 'pending' && (
                          <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                            {approval.reviewed_by ? `Reviewed by ${approval.reviewed_by}` : '-'}
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Card>

        {/* Review Dialog */}
        <Dialog
          open={reviewDialog.open}
          onClose={() => setReviewDialog({ open: false, approval: null, action: 'approve' })}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ fontWeight: 700 }}>
            {reviewDialog.action === 'approve' ? 'Approve Request' : 'Reject Request'}
          </DialogTitle>
          <DialogContent>
            <TextField
              label="Comment (optional)"
              fullWidth
              multiline
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button
              onClick={() => setReviewDialog({ open: false, approval: null, action: 'approve' })}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color={reviewDialog.action === 'approve' ? 'success' : 'error'}
              onClick={handleSubmitReview}
            >
              {reviewDialog.action === 'approve' ? 'Approve' : 'Reject'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default ApprovalsPage;
