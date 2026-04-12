import { ExpandLess, ExpandMore, FiberManualRecord } from '@mui/icons-material';
import { Box, Collapse, IconButton, Paper, Stack, Typography } from '@mui/material';
import { useMemo, useState } from 'react';

import { ConfigNode } from '@/types';

interface TreeNode extends ConfigNode {
  children: TreeNode[];
}

const buildTree = (nodes: ConfigNode[]): TreeNode[] => {
  const map = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];

  nodes.forEach((node) => map.set(node.config_node_id, { ...node, children: [] }));
  map.forEach((node) => {
    if (node.parent_config_node_id && map.has(node.parent_config_node_id)) {
      map.get(node.parent_config_node_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots.sort((a, b) => a.path.localeCompare(b.path));
};

const NodeRow = ({
  node,
  level,
  selectedId,
  onSelect,
}: {
  node: TreeNode;
  level: number;
  selectedId: string | null;
  onSelect: (node: ConfigNode) => void;
}) => {
  const [open, setOpen] = useState(true);
  const hasChildren = node.children.length > 0;
  const selected = selectedId === node.config_node_id;

  return (
    <Box>
      <Paper
        onClick={() => onSelect(node)}
        sx={{
          ml: level * 2,
          mt: 1,
          p: 1.5,
          cursor: 'pointer',
          background: selected ? 'linear-gradient(135deg, rgba(91,77,245,0.12) 0%, rgba(124,58,237,0.12) 100%)' : 'white',
          border: selected ? '1px solid rgba(91,77,245,0.35)' : '1px solid rgba(148,163,184,0.16)',
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <IconButton size="small" onClick={(event) => {
            event.stopPropagation();
            if (hasChildren) setOpen((value) => !value);
          }}>
            {hasChildren ? (open ? <ExpandLess /> : <ExpandMore />) : <FiberManualRecord sx={{ fontSize: 12 }} />}
          </IconButton>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              {node.path.split('/').filter(Boolean).slice(-1)[0] || '/'}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748b' }}>
              {node.path}
            </Typography>
          </Box>
        </Stack>
      </Paper>
      {hasChildren && (
        <Collapse in={open}>
          {node.children
            .sort((a, b) => a.path.localeCompare(b.path))
            .map((child) => (
              <NodeRow
                key={child.config_node_id}
                node={child}
                level={level + 1}
                selectedId={selectedId}
                onSelect={onSelect}
              />
            ))}
        </Collapse>
      )}
    </Box>
  );
};

export const ServiceTree = ({
  nodes,
  selectedId,
  onSelect,
}: {
  nodes: ConfigNode[];
  selectedId: string | null;
  onSelect: (node: ConfigNode) => void;
}) => {
  const tree = useMemo(() => buildTree(nodes), [nodes]);
  return (
    <Box>
      {tree.map((node) => (
        <NodeRow key={node.config_node_id} node={node} level={0} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </Box>
  );
};

