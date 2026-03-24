import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
} from '@mui/material';
import { Add, CheckCircle, Visibility, PlayArrow } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { apiClient } from '@/services/api';
import { useAppStore } from '@/stores/app';
import { ConfigVersion, ConfigItem } from '@/types';

const ConfigVersions = () => {
  const [versions, setLocalVersions] = useState<ConfigVersion[]>([]);
  const [configItems, setLocalConfigItems] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<ConfigVersion | null>(null);
  const currentUser = useAppStore((state: any) => state.currentUser);

  const [formData, setFormData] = useState({
    config_item_id: '',
    payload: '{}',
    change_summary: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const itemsRes = await apiClient.getConfigItems();
      setLocalConfigItems(itemsRes.data);

      // Fetch all versions for all items
      const allVersions: ConfigVersion[] = [];
      for (const item of itemsRes.data) {
        const versionsRes = await apiClient.getConfigVersions(item.id);
        allVersions.push(...versionsRes.data);
      }
      setLocalVersions(allVersions.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setSelectedVersion(null);
    setFormData({
      config_item_id: '',
      payload: '{}',
      change_summary: '',
    });
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedVersion(null);
  };

  const handleCreateVersion = async () => {
    try {
      if (!formData.config_item_id) {
        setError('Please select a config item');
        return;
      }

      await apiClient.createConfigVersion(parseInt(formData.config_item_id), {
        payload: JSON.parse(formData.payload),
        change_summary: formData.change_summary,
        created_by: currentUser,
        config_item: parseInt(formData.config_item_id),
        version_number: 0,
        checksum: '',
        status: 'draft',
        validation_error: '',
        id: 0,
        created_at: '',
      } as any);
      setOpenDialog(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create version');
      console.error('Error creating version:', err);
    }
  };

  const handleActivateVersion = async (version: ConfigVersion) => {
    try {
      await apiClient.activateConfigVersion(version.id, { actor: currentUser });
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to activate version');
      console.error('Error activating version:', err);
    }
  };

  const handleValidateVersion = async (version: ConfigVersion) => {
    try {
      await apiClient.validateConfigVersion(version.id, { actor: currentUser });
      setViewDialogOpen(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to validate version');
      console.error('Error validating version:', err);
    }
  };

  const handleArchiveVersion = async (version: ConfigVersion) => {
    try {
      await apiClient.archiveConfigVersion(version.id, { actor: currentUser });
      setViewDialogOpen(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to archive version');
      console.error('Error archiving version:', err);
    }
  };

  const handleViewVersion = (version: ConfigVersion) => {
    setSelectedVersion(version);
    setViewDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'warning' | 'success' | 'error' | 'info'> = {
      draft: 'warning',
      validated: 'info',
      validation_failed: 'error',
      active: 'success',
      archived: 'info',
    };
    return colors[status] as any || 'info';
  };

  return (
    <Layout>
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Box sx={{ fontSize: '28px' }}>📦</Box>
              <Box>
                <Box sx={{ fontSize: '24px', fontWeight: 800 }}>Config Versions</Box>
                <Box sx={{ fontSize: '14px', color: '#64748b' }}>Manage and activate configuration versions</Box>
              </Box>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleOpenDialog}
            sx={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            New Version
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, animation: 'slideIn 0.3s ease-out' }}>
            {error}
          </Alert>
        )}

        {/* Version Lifecycle */}
        <Card
          sx={{
            p: 3,
            background: 'linear-gradient(135deg, #f0f4ff 0%, #e9ecff 100%)',
            border: '1px solid #c7d2fe',
            mb: 4,
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#4f46e5', mb: 1 }}>
            Version Lifecycle
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            {['DRAFT', 'VALIDATED', 'ACTIVE', 'ARCHIVED'].map((status, i) => (
              <Box key={status} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={status} size="small" sx={{ fontWeight: 600 }} />
                {i < 3 && <Typography sx={{ color: '#4f46e5', fontWeight: 700 }}>→</Typography>}
              </Box>
            ))}
          </Box>
        </Card>

        {/* Versions Table */}
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
          ) : versions.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center', color: '#94a3b8' }}>
              <Box sx={{ fontSize: '48px', mb: 2 }}>📦</Box>
              <Box>No versions yet. Create your first version to get started!</Box>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: '#f8fafc' }}>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Config Item</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Version</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Change Summary</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Created</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }} align="right">
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {versions.map((version) => (
                    <TableRow
                      key={version.id}
                      sx={{
                        '&:hover': { background: '#f8fafc' },
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>
                        {configItems.find(i => i.id === version.config_item)?.key}
                      </TableCell>
                      <TableCell sx={{ color: '#64748b' }}>v{version.version_number}</TableCell>
                      <TableCell>
                        <Chip
                          label={version.status.toUpperCase()}
                          color={getStatusColor(version.status)}
                          variant="outlined"
                          size="small"
                          icon={version.status === 'active' ? <CheckCircle /> : undefined}
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#64748b', maxWidth: 250 }}>
                        {version.change_summary}
                      </TableCell>
                      <TableCell sx={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                        {new Date(version.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                          <Button
                            size="small"
                            startIcon={<Visibility />}
                            onClick={() => handleViewVersion(version)}
                            variant="outlined"
                            sx={{ textTransform: 'none' }}
                          >
                            View
                          </Button>
                          {version.status === 'validated' && (
                            <Button
                              size="small"
                              startIcon={<PlayArrow />}
                              onClick={() => handleActivateVersion(version)}
                              variant="contained"
                              sx={{
                                textTransform: 'none',
                                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                              }}
                            >
                              Activate
                            </Button>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Card>

        {/* Create Dialog */}
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 700, fontSize: '18px' }}>
            Create New Config Version
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Config Item</InputLabel>
                  <Select
                    value={formData.config_item_id}
                    label="Config Item"
                    onChange={(e) => setFormData({ ...formData, config_item_id: e.target.value })}
                  >
                    {configItems.map((item) => (
                      <MenuItem key={item.id} value={item.id}>
                        {item.key} ({item.scope_level})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Change Summary"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.change_summary}
                  onChange={(e) => setFormData({ ...formData, change_summary: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Payload (JSON)"
                  fullWidth
                  multiline
                  rows={8}
                  value={formData.payload}
                  onChange={(e) => setFormData({ ...formData, payload: e.target.value })}
                  sx={{ fontFamily: 'monospace', fontSize: '12px' }}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleCreateVersion}
              disabled={!formData.config_item_id}
              sx={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              Create
            </Button>
          </DialogActions>
        </Dialog>

        {/* View Dialog */}
        <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 700, fontSize: '18px' }}>
            Version #{selectedVersion?.version_number}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ color: '#64748b' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#4f46e5' }}>
                    Status
                  </Typography>
                  <Chip
                    label={selectedVersion?.status.toUpperCase()}
                    color={getStatusColor(selectedVersion?.status || 'draft')}
                    variant="outlined"
                    size="small"
                    sx={{ mt: 0.5 }}
                  />
                </Box>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box sx={{ color: '#64748b' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#4f46e5' }}>
                    Checksum
                  </Typography>
                  <Typography sx={{ fontFamily: 'monospace', fontSize: '11px' }}>
                    {selectedVersion?.checksum}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ color: '#64748b' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#4f46e5' }}>
                    Payload
                  </Typography>
                  <Box
                    sx={{
                      background: '#f8fafc',
                      p: 2,
                      borderRadius: '8px',
                      fontFamily: 'monospace',
                      fontSize: '12px',
                      overflow: 'auto',
                      maxHeight: '300px',
                      whiteSpace: 'pre-wrap',
                      wordWrap: 'break-word',
                    }}
                  >
                    {JSON.stringify(selectedVersion?.payload, null, 2)}
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {selectedVersion?.status === 'draft' && (
                <Button
                  variant="contained"
                  onClick={() => selectedVersion && handleValidateVersion(selectedVersion)}
                  sx={{
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  Validate
                </Button>
              )}
              {selectedVersion?.status === 'validated' && (
                <Button
                  variant="contained"
                  onClick={() => selectedVersion && handleActivateVersion(selectedVersion)}
                  sx={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  Activate
                </Button>
              )}
              {selectedVersion?.status === 'active' && (
                <Button
                  variant="outlined"
                  onClick={() => selectedVersion && handleArchiveVersion(selectedVersion)}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                    color: '#ef4444',
                    borderColor: '#ef4444',
                    '&:hover': {
                      borderColor: '#dc2626',
                      backgroundColor: '#fee2e2',
                    },
                  }}
                >
                  Archive
                </Button>
              )}
            </Box>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default ConfigVersions;
