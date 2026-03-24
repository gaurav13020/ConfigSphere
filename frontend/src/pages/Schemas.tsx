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
} from '@mui/material';
import { Add, Visibility, Edit, Delete } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { apiClient } from '@/services/api';
import { Schema as SchemaType } from '@/types';

const Schemas = () => {
  const [schemas, setLocalSchemas] = useState<SchemaType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedSchema, setSelectedSchema] = useState<SchemaType | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    schema_json: '{}',
  });

  useEffect(() => {
    fetchSchemas();
  }, []);

  const fetchSchemas = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getSchemas();
      setLocalSchemas(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch schemas');
      console.error('Error fetching schemas:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (schema?: SchemaType) => {
    if (schema) {
      setSelectedSchema(schema);
      setFormData({
        name: schema.name,
        description: schema.description,
        schema_json: JSON.stringify(schema.schema_json, null, 2),
      });
    } else {
      setSelectedSchema(null);
      setFormData({ name: '', description: '', schema_json: '{}' });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedSchema(null);
  };

  const handleCreateSchema = async () => {
    try {
      setLoading(true);
      const data = {
        name: formData.name,
        description: formData.description,
        schema_json: JSON.parse(formData.schema_json),
      };

      if (selectedSchema) {
        // Update existing schema
        await apiClient.updateSchema(selectedSchema.id, data as any);
      } else {
        // Create new schema
        await apiClient.createSchema(data as any);
      }
      setOpenDialog(false);
      fetchSchemas();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to save schema');
      console.error('Error saving schema:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSchema = async (schema: SchemaType) => {
    if (!window.confirm(`Are you sure you want to delete the schema "${schema.name}"?`)) {
      return;
    }

    try {
      setLoading(true);
      await apiClient.deleteSchema(schema.id);
      fetchSchemas();
    } catch (err: any) {
      let errorMsg = err.response?.data?.message || 'Failed to delete schema';
      
      // Check if we have error details from backend
      if (err.response?.data?.error) {
        errorMsg = err.response.data.error;
      }
      
      setError(errorMsg);
      console.error('Error deleting schema:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewSchema = (schema: SchemaType) => {
    setSelectedSchema(schema);
    setViewDialogOpen(true);
  };

  return (
    <Layout>
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Box sx={{ fontSize: '28px' }}>📋</Box>
              <Box>
                <Box sx={{ fontSize: '24px', fontWeight: 800 }}>Schemas</Box>
                <Box sx={{ fontSize: '14px', color: '#64748b' }}>Manage JSON Schema definitions</Box>
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
            New Schema
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, animation: 'slideIn 0.3s ease-out' }}>
            {error}
          </Alert>
        )}

        {/* Schemas Table */}
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
          ) : schemas.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center', color: '#94a3b8' }}>
              <Box sx={{ fontSize: '48px', mb: 2 }}>📭</Box>
              <Box>No schemas yet. Create your first schema to get started!</Box>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: '#f8fafc' }}>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Description</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Created</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }} align="right">
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {schemas.map((schema: any) => (
                    <TableRow
                      key={schema.id}
                      sx={{
                        '&:hover': { background: '#f8fafc' },
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>{schema.name}</TableCell>
                      <TableCell sx={{ color: '#64748b', maxWidth: 300 }}>
                        {schema.description.substring(0, 50)}
                        {schema.description.length > 50 ? '...' : ''}
                      </TableCell>
                      <TableCell sx={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                        {new Date(schema.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                          <Button
                            size="small"
                            startIcon={<Visibility />}
                            onClick={() => handleViewSchema(schema)}
                            variant="outlined"
                            sx={{ textTransform: 'none' }}
                          >
                            View
                          </Button>
                          <Button
                            size="small"
                            startIcon={<Edit />}
                            onClick={() => handleOpenDialog(schema)}
                            variant="outlined"
                            sx={{ textTransform: 'none', color: '#f59e0b', borderColor: '#f59e0b' }}
                          >
                            Edit
                          </Button>
                          <Button
                            size="small"
                            startIcon={<Delete />}
                            onClick={() => handleDeleteSchema(schema)}
                            variant="outlined"
                            sx={{ textTransform: 'none', color: '#ef4444', borderColor: '#ef4444' }}
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
            {selectedSchema ? 'Edit Schema' : 'Create New Schema'}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Schema Name"
                  fullWidth
                  value={formData.name}
                  onChange={(e: any) => setFormData({ ...formData, name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Description"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.description}
                  onChange={(e: any) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="JSON Schema"
                  fullWidth
                  multiline
                  rows={8}
                  value={formData.schema_json}
                  onChange={(e: any) => setFormData({ ...formData, schema_json: e.target.value })}
                  sx={{ fontFamily: 'monospace', fontSize: '12px' }}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleCreateSchema}
              disabled={!formData.name}
              sx={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              {selectedSchema ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* View Schema Dialog */}
        <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 700, fontSize: '18px' }}>
            {selectedSchema?.name}
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Box sx={{ color: '#64748b', mb: 2 }}>
                  <Box sx={{ fontWeight: 600, mb: 0.5 }}>Description</Box>
                  <Box>{selectedSchema?.description}</Box>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ color: '#64748b' }}>
                  <Box sx={{ fontWeight: 600, mb: 0.5 }}>JSON Schema</Box>
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
                    {JSON.stringify(selectedSchema?.schema_json, null, 2)}
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

export default Schemas;
