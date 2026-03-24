import { useState } from 'react';
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
  Typography,
} from '@mui/material';
import { Search } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { apiClient } from '@/services/api';
import { ResolvedConfig } from '@/types';

const ResolvedConfigResolver = () => {
  const [resolvedConfig, setLocalResolvedConfig] = useState<ResolvedConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);

  const [filterParams, setFilterParams] = useState({
    global: 'default',
    region: '',
    group: '',
    service: '',
  });

  const handleResolve = async () => {
    try {
      setLoading(true);
      setError(null);

      const query: Record<string, any> = {
        global: filterParams.global,
      };

      if (filterParams.region) query.region = filterParams.region;
      if (filterParams.group) query.group = filterParams.group;
      if (filterParams.service) query.service = filterParams.service;

      const response = await apiClient.getResolvedConfig(query);
      setLocalResolvedConfig(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to resolve config');
      console.error('Error resolving config:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScopeColor = (scope: string) => {
    const colors: Record<string, string> = {
      global: '#4f46e5',
      region: '#7c3aed',
      group: '#f59e0b',
      service: '#ef4444',
    };
    return colors[scope] || '#64748b';
  };

  return (
    <Layout>
      <Box>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Box sx={{ fontSize: '28px' }}>🔍</Box>
            <Box>
              <Box sx={{ fontSize: '24px', fontWeight: 800 }}>Config Resolver</Box>
              <Box sx={{ fontSize: '14px', color: '#64748b' }}>
                Resolve merged effective configuration across hierarchy levels
              </Box>
            </Box>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, animation: 'slideIn 0.3s ease-out' }}>
            {error}
          </Alert>
        )}

        {/* Filter Card */}
        <Card
          sx={{
            p: 4,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            border: '1px solid #e2e8f0',
            mb: 4,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
            Select Scope Level
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Global Name"
                fullWidth
                value={filterParams.global}
                onChange={(e) =>
                  setFilterParams({ ...filterParams, global: e.target.value })
                }
                placeholder="default"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Region Name"
                fullWidth
                value={filterParams.region}
                onChange={(e) =>
                  setFilterParams({ ...filterParams, region: e.target.value })
                }
                placeholder="e.g., us-west"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Group Name"
                fullWidth
                value={filterParams.group}
                onChange={(e) =>
                  setFilterParams({ ...filterParams, group: e.target.value })
                }
                placeholder="e.g., payment-team"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Service Name"
                fullWidth
                value={filterParams.service}
                onChange={(e) =>
                  setFilterParams({ ...filterParams, service: e.target.value })
                }
                placeholder="e.g., payment-service"
              />
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<Search />}
              onClick={handleResolve}
              disabled={loading}
              sx={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              {loading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
              Resolve Config
            </Button>
          </Box>
        </Card>

        {/* Results */}
        {resolvedConfig && (
          <>
            {/* Summary Card */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Card
                  sx={{
                    p: 3,
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 600 }}>
                    Checksum
                  </Typography>
                  <Typography
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '12px',
                      mt: 1,
                      color: '#4f46e5',
                      fontWeight: 600,
                    }}
                  >
                    {resolvedConfig.checksum.substring(0, 16)}...
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card
                  sx={{
                    p: 3,
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 600 }}>
                    Layers
                  </Typography>
                  <Typography sx={{ fontSize: '28px', fontWeight: 800, mt: 1 }}>
                    {resolvedConfig.layers.length}
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card
                  sx={{
                    p: 3,
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 600 }}>
                    Keys
                  </Typography>
                  <Typography sx={{ fontSize: '28px', fontWeight: 800, mt: 1 }}>
                    {Object.keys(resolvedConfig.payload).length}
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card
                  sx={{
                    p: 3,
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => setViewDialogOpen(true)}
                    sx={{ textTransform: 'none', fontWeight: 600 }}
                  >
                    View Full
                  </Button>
                </Card>
              </Grid>
            </Grid>

            {/* Hierarchy Layers */}
            <Card
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                border: '1px solid #e2e8f0',
                mb: 4,
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                Hierarchy Layers
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ background: '#f8fafc' }}>
                      <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Scope Level</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Config Item</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Version</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Checksum</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {resolvedConfig.layers.map((layer, idx) => (
                      <TableRow key={idx}>
                        <TableCell>
                          <Chip
                            label={layer.scope_level.toUpperCase()}
                            size="small"
                            sx={{
                              background: `${getScopeColor(layer.scope_level)}20`,
                              color: getScopeColor(layer.scope_level),
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>
                          {layer.key} (ID: {layer.config_item_id})
                        </TableCell>
                        <TableCell sx={{ color: '#64748b' }}>v{layer.version_number}</TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '12px', color: '#4f46e5' }}>
                          {layer.checksum.substring(0, 16)}...
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Card>

            {/* Merged Payload Preview */}
            <Card
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                border: '1px solid #e2e8f0',
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Merged Configuration
              </Typography>
              <Box
                sx={{
                  background: '#f8fafc',
                  p: 3,
                  borderRadius: '8px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  overflow: 'auto',
                  maxHeight: '400px',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                }}
              >
                {JSON.stringify(resolvedConfig.payload, null, 2)}
              </Box>
            </Card>
          </>
        )}

        {/* Full View Dialog */}
        <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="lg" fullWidth>
          <DialogTitle sx={{ fontWeight: 700, fontSize: '18px' }}>
            Resolved Configuration
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Box
              sx={{
                background: '#f8fafc',
                p: 3,
                borderRadius: '8px',
                fontFamily: 'monospace',
                fontSize: '12px',
                overflow: 'auto',
                maxHeight: '600px',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
              }}
            >
              {JSON.stringify(resolvedConfig, null, 2)}
            </Box>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default ResolvedConfigResolver;
