import { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Add, Schema, Settings, History, VisibilityOff } from '@mui/icons-material';
import { Layout } from '@/components/Layout';
import { StatsCard } from '@/components/StatsCard';
import { apiClient } from '@/services/api';
import { useAppStore } from '@/stores/app';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    schemas: 0,
    configItems: 0,
    versions: 0,
    auditEvents: 0,
  });
  const [recentEvents, setRecentEvents] = useState<any[]>([]);

  const setSchemas = useAppStore((state: any) => state.setSchemas);
  const setConfigItems = useAppStore((state: any) => state.setConfigItems);
  const setConfigVersions = useAppStore((state: any) => state.setConfigVersions);
  const setAuditEvents = useAppStore((state: any) => state.setAuditEvents);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [schemasRes, itemsRes, auditRes] = await Promise.all([
          apiClient.getSchemas(),
          apiClient.getConfigItems(),
          apiClient.getAuditEvents({ ordering: '-created_at' }),
        ]);

        setSchemas(schemasRes.data);
        setConfigItems(itemsRes.data);
        setAuditEvents(auditRes.data);
        setRecentEvents(auditRes.data.slice(0, 5));

        setStats({
          schemas: schemasRes.data.length,
          configItems: itemsRes.data.length,
          versions: itemsRes.data.reduce((acc: number) => acc + 1, 0),
          auditEvents: auditRes.data.length,
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [setSchemas, setConfigItems, setConfigVersions, setAuditEvents]);

  const getEventColor = (eventType: string) => {
    const colors: Record<string, string> = {
      schema_created: 'info',
      config_item_created: 'success',
      config_version_created: 'primary',
      validation_passed: 'success',
      validation_failed: 'error',
      version_activated: 'success',
      version_archived: 'warning',
      resolved_config_fetched: 'info',
    };
    return colors[eventType] || 'default';
  };

  return (
    <Layout>
      <Box>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1 }}>
            Dashboard
          </Typography>
          <Typography variant="body1" sx={{ color: '#64748b' }}>
            Welcome to ConfigSphere. Manage your configurations across the hierarchy.
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Schemas"
              value={stats.schemas}
              icon={<Schema />}
              loading={loading}
              color="#4f46e5"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Config Items"
              value={stats.configItems}
              icon={<Settings />}
              loading={loading}
              color="#7c3aed"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Total Events"
              value={stats.auditEvents}
              icon={<History />}
              loading={loading}
              color="#06b6d4"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Hierarchy Levels"
              value={4}
              icon={<VisibilityOff />}
              color="#f59e0b"
            />
          </Grid>
        </Grid>

        {/* Quick Actions */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6}>
            <Card
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                border: '1px solid #e2e8f0',
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: '0 10px 40px rgba(79, 70, 229, 0.1)',
                },
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => navigate('/schemas')}
                  sx={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  New Schema
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={() => navigate('/config-items')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  New Config Item
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={() => navigate('/resolver')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  Resolve Config
                </Button>
              </Box>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Card
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                border: '1px solid #e2e8f0',
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                System Info
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748b' }}>API URL:</Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                    localhost:8000
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748b' }}>Hierarchy Levels:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>global → region → group → service</Typography>
                </Box>
              </Box>
            </Card>
          </Grid>
        </Grid>

        {/* Recent Events */}
        <Card
          sx={{
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            border: '1px solid #e2e8f0',
          }}
        >
          <Box sx={{ p: 3, borderBottom: '1px solid #e2e8f0' }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Recent Activity
            </Typography>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : recentEvents.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center', color: '#94a3b8' }}>
              <Typography>No events yet</Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: '#f8fafc' }}>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Event Type</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Actor</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: '#4f46e5' }}>Timestamp</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentEvents.map((event: any) => (
                    <TableRow key={event.id}>
                      <TableCell>
                        <Chip
                          label={event.event_type}
                          color={getEventColor(event.event_type) as any}
                          variant="outlined"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{event.actor || '-'}</TableCell>
                      <TableCell sx={{ color: '#64748b', fontSize: '0.85rem' }}>
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

export default Dashboard;
