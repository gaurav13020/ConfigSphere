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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Typography,
} from '@mui/material';
import { Add, Visibility, Edit, Delete } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { apiClient } from '@/services/api';
import { ConfigItem as ConfigItemType, Schema } from '@/types';

const ConfigItems = () => {
  const [configItems, setLocalConfigItems] = useState<ConfigItemType[]>([]);
  const [schemas, setLocalSchemas] = useState<Schema[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ConfigItemType | null>(null);

  const [formData, setFormData] = useState({
    key: '',
    scope_level: 'global' as 'global' | 'region' | 'group' | 'service',
    global_name: 'default',
    region_name: '',
    group_name: '',
    service_name: '',
    schema_id: '',
    description: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [itemsRes, schemasRes] = await Promise.all([
        apiClient.getConfigItems(),
        apiClient.getSchemas(),
      ]);
      setLocalConfigItems(itemsRes.data);
      setLocalSchemas(schemasRes.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (item?: ConfigItemType) => {
    if (item) {
      setSelectedItem(item);
      setFormData({
        key: item.key,
        scope_level: item.scope_level,
        global_name: item.global_name,
        region_name: item.region_name,
        group_name: item.group_name,
        service_name: item.service_name,
        schema_id: item.schema?.toString() || '',
        description: item.description,
      });
    } else {
      setSelectedItem(null);
      setFormData({
        key: '',
        scope_level: 'global',
        global_name: 'default',
        region_name: '',
        group_name: '',
        service_name: '',
        schema_id: '',
        description: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedItem(null);
  };

  const handleCreateItem = async () => {
    try {
      setLoading(true);
      const payload: any = {
        key: formData.key,
        scope_level: formData.scope_level,
        description: formData.description,
        global_name: formData.global_name,
      };

      if (formData.scope_level === 'region') {
        payload.region_name = formData.region_name;
      } else if (formData.scope_level === 'group') {
        payload.region_name = formData.region_name;
        payload.group_name = formData.group_name;
      } else if (formData.scope_level === 'service') {
        payload.service_name = formData.service_name;
      }

      if (formData.schema_id) {
        payload.schema_id = parseInt(formData.schema_id);
      }

      if (selectedItem) {
        await apiClient.updateConfigItem(selectedItem.id, payload);
      } else {
        await apiClient.createConfigItem(payload);
      }
      setOpenDialog(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to save config item');
      console.error('Error saving config item:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfigItem = async (item: ConfigItemType) => {
    if (window.confirm(`Are you sure you want to delete the config item "${item.key}"?`)) {
      try {
        setLoading(true);
        await apiClient.deleteConfigItem(item.id);
        fetchData();
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Failed to delete config item';
        setError(errorMessage);
        console.error('Error deleting config item:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleViewItem = (item: ConfigItemType) => {
    setSelectedItem(item);
    setViewDialogOpen(true);
  };

  const getScopeBadgeColor = (scope: string) => {
    const colors: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
      global: 'info',
      region: 'success',
      group: 'warning',
      service: 'error',
    };
    return colors[scope] || 'default';
  };

  return (
    <Layout>
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Box sx={{ fontSize: '28px' }}>⚙️</Box>
              <Box>
                <Box sx={{ fontSize: '24px', fontWeight: 800 }}>Config Items</Box>
                <Box sx={{ fontSize: '14px', color: '#64748b' }}>Manage configuration items across hierarchy levels</Box>
              </Box>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleOpenDialog()}
            sx={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            New Config Item
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, animation: 'slideIn 0.3s ease-out' }}>
            {error}
          </Alert>
        )}

        {/* Hierarchy Info */}
        <Card
          sx={{
            p: 3,
            background: 'linear-gradient(135deg, #f0f4ff 0%, #e9ecff 100%)',
            border: '1px solid #c7d2fe',
            mb: 4,
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#4f46e5', mb: 1 }}>
            Hierarchy Precedence
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            {['service', 'group', 'region', 'global'].map((level, i) => (
              <Box key={level} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={level} variant="outlined" size="small" sx={{ fontWeight: 600 }} />
                {i < 3 && <Typography sx={{ color: '#4f46e5', fontWeight: 700 }}>&gt;</Typography>}
              </Box>
            ))}
          </Box>
        </Card>

        {/* Config Items Table */}
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
          ) : configItems.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center', color: '#94a3b8' }}>
              <Box sx={{ fontSize: '48px', mb: 2 }}>📭</Box>
              <Box>No config items yet. Create your first item to get started!</Box>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: '#f8fafc' }}>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Key</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Scope Level</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Scope Details</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Schema</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }} align="right">
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {configItems.map((item: any) => (
                    <TableRow
                      key={item.id}
                      sx={{
                        '&:hover': { background: '#f8fafc' },
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>{item.key}</TableCell>
                      <TableCell>
                        <Chip
                          label={item.scope_level.toUpperCase()}
                          color={getScopeBadgeColor(item.scope_level) as any}
                          variant="outlined"
                          size="small"
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#64748b', fontSize: '0.85rem', fontFamily: 'monospace' }}>
                        {item.scope_level === 'global' && item.global_name}
                        {item.scope_level === 'region' && `${item.global_name} / ${item.region_name}`}
                        {item.scope_level === 'group' && `${item.global_name} / ${item.region_name} / ${item.group_name}`}
                        {item.scope_level === 'service' && item.service_name}
                      </TableCell>
                      <TableCell sx={{ color: '#94a3b8' }}>
                        {item.schema ? <Chip label={`Schema #${item.schema}`} size="small" /> : '-'}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                          <Button
                            size="small"
                            startIcon={<Visibility />}
                            onClick={() => handleViewItem(item)}
                            variant="outlined"
                            sx={{ textTransform: 'none' }}
                          >
                            View
                          </Button>
                          <Button
                            size="small"
                            startIcon={<Edit />}
                            onClick={() => handleOpenDialog(item)}
                            variant="outlined"
                            sx={{ textTransform: 'none' }}
                          >
                            Edit
                          </Button>
                          <Button
                            size="small"
                            startIcon={<Delete />}
                            onClick={() => handleDeleteConfigItem(item)}
                            variant="outlined"
                            color="error"
                            sx={{ textTransform: 'none' }}
                          >
                            Delete
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Card>

        {/* Create/Edit Dialog */}
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 700, fontSize: '18px' }}>
            {selectedItem ? 'Edit Config Item' : 'Create New Config Item'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Config Key"
                  fullWidth
                  value={formData.key}
                  onChange={(e: any) => setFormData({ ...formData, key: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Scope Level</InputLabel>
                  <Select
                    value={formData.scope_level}
                    label="Scope Level"
                    onChange={(e: any) => setFormData({ ...formData, scope_level: e.target.value as any })}
                  >
                    <MenuItem value="global">Global</MenuItem>
                    <MenuItem value="region">Region</MenuItem>
                    <MenuItem value="group">Group</MenuItem>
                    <MenuItem value="service">Service</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {['global', 'region', 'group'].includes(formData.scope_level) && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Global Name"
                    fullWidth
                    value={formData.global_name}
                    onChange={(e: any) => setFormData({ ...formData, global_name: e.target.value })}
                  />
                </Grid>
              )}

              {['region', 'group'].includes(formData.scope_level) && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Region Name"
                    fullWidth
                    value={formData.region_name}
                    onChange={(e: any) => setFormData({ ...formData, region_name: e.target.value })}
                  />
                </Grid>
              )}

              {formData.scope_level === 'group' && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Group Name"
                    fullWidth
                    value={formData.group_name}
                    onChange={(e: any) => setFormData({ ...formData, group_name: e.target.value })}
                  />
                </Grid>
              )}

              {formData.scope_level === 'service' && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Service Name"
                    fullWidth
                    value={formData.service_name}
                    onChange={(e: any) => setFormData({ ...formData, service_name: e.target.value })}
                  />
                </Grid>
              )}

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Schema (Optional)</InputLabel>
                  <Select
                    value={formData.schema_id}
                    label="Schema (Optional)"
                    onChange={(e: any) => setFormData({ ...formData, schema_id: e.target.value })}
                  >
                    <MenuItem value="">None</MenuItem>
                    {schemas.map((schema: any) => (
                      <MenuItem key={schema.id} value={schema.id}>
                        {schema.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Description"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleCreateItem}
              disabled={!formData.key || !formData.scope_level}
              sx={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              {selectedItem ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* View Item Dialog */}
        <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 700, fontSize: '18px' }}>
            {selectedItem?.key}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ color: '#64748b' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#4f46e5' }}>
                    Scope Level
                  </Typography>
                  <Typography>{selectedItem?.scope_level.toUpperCase()}</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box sx={{ color: '#64748b' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#4f46e5' }}>
                    Description
                  </Typography>
                  <Typography>{selectedItem?.description}</Typography>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ color: '#64748b' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#4f46e5' }}>
                    Scope Details
                  </Typography>
                  <Box sx={{ background: '#f8fafc', p: 2, borderRadius: '8px', fontFamily: 'monospace', fontSize: '12px' }}>
                    global: {selectedItem?.global_name}
                    <br />
                    region: {selectedItem?.region_name || '-'}
                    <br />
                    group: {selectedItem?.group_name || '-'}
                    <br />
                    service: {selectedItem?.service_name || '-'}
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default ConfigItems;
