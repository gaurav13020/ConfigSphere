import { useEffect, useState } from 'react';
import {
  Box,
  Card,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Download } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { apiClient } from '@/services/api';
import { AuditEvent } from '@/types';

const AuditTrail = () => {
  const [events, setLocalEvents] = useState<AuditEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    eventType: '',
    actor: '',
    dateFrom: '',
    dateTo: '',
  });

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [events, filters]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getAuditEvents({ ordering: '-created_at' });
      setLocalEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...events];

    if (filters.eventType) {
      filtered = filtered.filter((e) => e.event_type === filters.eventType);
    }

    if (filters.actor) {
      filtered = filtered.filter((e) =>
        e.actor?.toLowerCase().includes(filters.actor.toLowerCase())
      );
    }

    if (filters.dateFrom) {
      filtered = filtered.filter((e) => new Date(e.created_at) >= new Date(filters.dateFrom));
    }

    if (filters.dateTo) {
      filtered = filtered.filter((e) => new Date(e.created_at) <= new Date(filters.dateTo));
    }

    setFilteredEvents(filtered);
  };

  const getEventIcon = (eventType: string) => {
    const icons: Record<string, string> = {
      schema_created: '📋',
      config_item_created: '⚙️',
      config_version_created: '📦',
      validation_passed: '✅',
      validation_failed: '❌',
      version_activated: '🚀',
      version_archived: '📁',
      resolved_config_fetched: '🔍',
    };
    return icons[eventType] || '📝';
  };

  const getEventColor = (eventType: string) => {
    const colors: Record<string, 'info' | 'success' | 'error' | 'warning'> = {
      schema_created: 'info',
      config_item_created: 'success',
      config_version_created: 'info',
      validation_passed: 'success',
      validation_failed: 'error',
      version_activated: 'success',
      version_archived: 'warning',
      resolved_config_fetched: 'info',
    };
    return colors[eventType] || 'default';
  };

  const handleExport = () => {
    const csv = [
      ['Event Type', 'Actor', 'Timestamp', 'Config Item ID', 'Config Version ID'].join(','),
      ...filteredEvents.map((e) =>
        [e.event_type, e.actor || '-', e.created_at, e.config_item_id || '-', e.config_version_id || '-'].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const uniqueEventTypes = Array.from(new Set(events.map((e) => e.event_type)));
  const uniqueActors = Array.from(new Set(events.map((e) => e.actor).filter(Boolean)));

  return (
    <Layout>
      <Box>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Box sx={{ fontSize: '28px' }}>📜</Box>
            <Box>
              <Box sx={{ fontSize: '24px', fontWeight: 800 }}>Audit Trail</Box>
              <Box sx={{ fontSize: '14px', color: '#64748b' }}>
                View all system events and changes
              </Box>
            </Box>
          </Box>
        </Box>

        {/* Statistics */}
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
                Total Events
              </Typography>
              <Typography sx={{ fontSize: '28px', fontWeight: 800, mt: 1 }}>
                {events.length}
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
                Filtered
              </Typography>
              <Typography sx={{ fontSize: '28px', fontWeight: 800, mt: 1, color: '#4f46e5' }}>
                {filteredEvents.length}
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
                Event Types
              </Typography>
              <Typography sx={{ fontSize: '28px', fontWeight: 800, mt: 1 }}>
                {uniqueEventTypes.length}
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
                Actors
              </Typography>
              <Typography sx={{ fontSize: '28px', fontWeight: 800, mt: 1 }}>
                {uniqueActors.length}
              </Typography>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card
          sx={{
            p: 3,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            border: '1px solid #e2e8f0',
            mb: 4,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
            Filters
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={filters.eventType}
                  label="Event Type"
                  onChange={(e) => setFilters({ ...filters, eventType: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  {uniqueEventTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Actor</InputLabel>
                <Select
                  value={filters.actor}
                  label="Actor"
                  onChange={(e) => setFilters({ ...filters, actor: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  {uniqueActors.map((actor) => (
                    <MenuItem key={actor || 'unknown'} value={actor || ''}>
                      {actor || 'Unknown'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="From Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={filters.dateFrom}
                onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="To Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={filters.dateTo}
                onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
              />
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              sx={{ textTransform: 'none', fontWeight: 600 }}
              onClick={() =>
                setFilters({
                  eventType: '',
                  actor: '',
                  dateFrom: '',
                  dateTo: '',
                })
              }
            >
              Reset Filters
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExport}
              sx={{ textTransform: 'none', fontWeight: 600 }}
            >
              Export CSV
            </Button>
          </Box>
        </Card>

        {/* Events Table */}
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
          ) : filteredEvents.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center', color: '#94a3b8' }}>
              <Box sx={{ fontSize: '48px', mb: 2 }}>📭</Box>
              <Box>No events match your filters</Box>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: '#f8fafc' }}>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Event</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Actor</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Config Item</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Timestamp</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredEvents.map((event) => (
                    <TableRow
                      key={event.id}
                      sx={{
                        '&:hover': { background: '#f8fafc' },
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ fontSize: '16px' }}>{getEventIcon(event.event_type)}</Box>
                          <Chip
                            label={event.event_type}
                            color={getEventColor(event.event_type)}
                            variant="outlined"
                            size="small"
                          />
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{event.actor || '-'}</TableCell>
                      <TableCell sx={{ color: '#64748b', fontSize: '0.85rem' }}>
                        {event.config_item_id ? `Item #${event.config_item_id}` : '-'}
                      </TableCell>
                      <TableCell sx={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                        {new Date(event.created_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Card>
      </Box>
    </Layout>
  );
};

export default AuditTrail;
