import { useState, useEffect, useRef } from 'react';
import './AdminDashboard.css';
import { config } from '../config';

interface FreshnessData {
  id: number;
  inventory_id: number;
  freshness_score: number;
  predicted_expiry_date?: string | null;
  confidence_level?: number;
  discount_percentage: number;
  status: string;
  last_checked?: string;
  image_url?: string | null;
  notes?: string | null;
}

interface InventoryItem {
  id: number;
  store_id: number;
  fruit_type: string;
  variety?: string;
  quantity: number;
  batch_number?: string;
  location_in_store?: string;
  arrival_date?: string;
  original_price: number;
  current_price: number;
  discount_percentage?: number;
  freshness?: FreshnessData;
  created_at: string;
  updated_at: string;
}

interface QuantityChange {
  inventory_id: number;
  fruit_type: string;
  old_quantity: number;
  new_quantity: number;
  delta: number;
  change_type: 'increase' | 'decrease';
  freshness_score?: number | null;
  timestamp: string;
}

interface DetectionImage {
  path: string;
  filename: string;
  timestamp: string;
  metadata?: {
    confidence?: number;
    freshness_score?: number;
    bbox?: number[];
    blemishes?: {
      bboxes?: Array<{
        box_2d: [number, number, number, number];
        label: string;
      }>;
      labels?: string[];
      count?: number;
      error?: string;
    };
  };
}

const InventoryView = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [quantityChanges, setQuantityChanges] = useState<QuantityChange[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [defaultStoreId, setDefaultStoreId] = useState<number | null>(null);
  const [selectedItemImages, setSelectedItemImages] = useState<DetectionImage[]>([]);
  const [selectedItemCategory, setSelectedItemCategory] = useState<string | null>(null);
  const [showImageModal, setShowImageModal] = useState(false);
  const [loadingImages, setLoadingImages] = useState(false);
  const [expandedImage, setExpandedImage] = useState<DetectionImage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Load initial inventory
    fetchInventory();
    fetchDefaultStore();

    // Connect to admin WebSocket
    const websocket = new WebSocket(`${config.wsUrl}/ws/admin`);
    wsRef.current = websocket;

    websocket.onopen = () => {
      setIsConnected(true);
      setConnectionError(null);
      // Request current stats to get initial data
      websocket.send(JSON.stringify({ action: 'get_stats' }));
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    websocket.onclose = () => {
      setIsConnected(false);
    };

    websocket.onerror = () => {
      setConnectionError('WebSocket connection error');
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await fetch(`${config.apiUrl}/api/inventory`);
      if (response.ok) {
        const data = await response.json();
        setInventory(data.items || []);
      }
    } catch (e) {
      console.error('Failed to fetch inventory:', e);
    }
  };

  const fetchDefaultStore = async () => {
    try {
      const response = await fetch(`${config.apiUrl}/api/stores`);
      if (response.ok) {
        const data = await response.json();
        if (data.stores && data.stores.length > 0) {
          setDefaultStoreId(data.stores[0].id);
        }
      }
    } catch (e) {
      console.error('Failed to fetch stores:', e);
    }
  };

  const fetchCategoryImages = async (category: string) => {
    setLoadingImages(true);
    setSelectedItemCategory(category);
    setShowImageModal(true); // Open modal immediately to show loading state
    try {
      const response = await fetch(`${config.apiUrl}/api/detection-images/${category}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedItemImages(data.images || []);
      } else {
        // No images found, still show modal with empty state
        setSelectedItemImages([]);
      }
    } catch (e) {
      console.error('Failed to fetch category images:', e);
      setSelectedItemImages([]);
    } finally {
      setLoadingImages(false);
    }
  };

  const handleFruitTypeClick = (fruitType: string) => {
    fetchCategoryImages(fruitType.toLowerCase());
  };

  const handleCreate = async (itemData: Partial<InventoryItem>) => {
    if (!defaultStoreId) {
      alert('No store available. Please create a store first.');
      return;
    }
    try {
      const response = await fetch(`${config.apiUrl}/api/inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          store_id: defaultStoreId,
          fruit_type: itemData.fruit_type,
          variety: itemData.variety || '',
          quantity: itemData.quantity || 0,
          batch_number: itemData.batch_number || '',
          location_in_store: itemData.location_in_store || '',
          original_price: itemData.original_price || 0,
          current_price: itemData.current_price || itemData.original_price || 0,
        }),
      });
      if (response.ok) {
        setShowCreateModal(false);
        fetchInventory();
      } else {
        const error = await response.json();
        alert(`Failed to create item: ${error.error || 'Unknown error'}`);
      }
    } catch (e) {
      console.error('Failed to create item:', e);
      alert('Failed to create item');
    }
  };

  const handleUpdate = async (itemId: number, itemData: Partial<InventoryItem>) => {
    try {
      const response = await fetch(`${config.apiUrl}/api/inventory/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(itemData),
      });
      if (response.ok) {
        setEditingItem(null);
        fetchInventory();
      } else {
        const error = await response.json();
        alert(`Failed to update item: ${error.error || 'Unknown error'}`);
      }
    } catch (e) {
      console.error('Failed to update item:', e);
      alert('Failed to update item');
    }
  };

  const handleDelete = async (itemId: number) => {
    try {
      const response = await fetch(`${config.apiUrl}/api/inventory/${itemId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchInventory();
      } else {
        const error = await response.json();
        alert(`Failed to delete item: ${error.error || 'Unknown error'}`);
      }
    } catch (e) {
      console.error('Failed to delete item:', e);
      alert('Failed to delete item');
    }
  };

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'quantity_changed') {
      // Add to quantity changes log
      const change: QuantityChange = {
        inventory_id: data.data.inventory_id,
        fruit_type: data.data.fruit_type,
        old_quantity: data.data.old_quantity,
        new_quantity: data.data.new_quantity,
        delta: data.data.delta,
        change_type: data.data.change_type,
        freshness_score: data.data.freshness_score,
        timestamp: data.timestamp || new Date().toISOString()
      };
      
      setQuantityChanges(prev => [change, ...prev].slice(0, 100)); // Keep last 100 changes
      
      // Update inventory item if it exists, otherwise refresh to get new items
      setInventory(prev => {
        const itemExists = prev.some(item => item.id === change.inventory_id);
        if (itemExists) {
          return prev.map(item => 
            item.id === change.inventory_id 
              ? { ...item, quantity: change.new_quantity }
              : item
          );
        } else {
          // Item doesn't exist yet, refresh to get it
          fetchInventory();
          return prev;
        }
      });
    } else if (data.type === 'freshness_updated') {
      // Update freshness score in real-time
      const inventoryId = data.data.inventory_id;
      const freshness = data.data.freshness;
      const item = data.data.item;
      
      setInventory(prev => prev.map(invItem => {
        if (invItem.id === inventoryId) {
          // Update freshness and also update price/discount if item data is provided
          return {
            ...invItem,
            freshness: freshness,
            // Update price and discount if provided in item data
            ...(item && {
              current_price: item.current_price,
              discount_percentage: item.discount_percentage
            })
          };
        }
        return invItem;
      }));
      
      console.log(`Freshness updated for item ${inventoryId}: ${freshness.freshness_score}%`);
    } else if (data.type === 'inventory_added') {
      // Refresh inventory to get new item
      fetchInventory();
    } else if (data.type === 'inventory_updated') {
      // Update inventory item
      if (data.data.id) {
        setInventory(prev => prev.map(item => 
          item.id === data.data.id 
            ? { ...item, ...data.data }
            : item
        ));
      }
    } else if (data.type === 'inventory_deleted') {
      // Remove item from inventory
      setInventory(prev => prev.filter(item => item.id !== data.data.id));
    }
  };

  const goBack = () => {
    window.location.hash = '#admin';
  };

  return (
    <div className="admin-dashboard inventory-view">
      <div className="admin-dashboard-header">
        <h1 className="admin-dashboard-title">INVENTORY MANAGEMENT</h1>
        <div className="status-indicators">
          <span className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
          <button className="control-btn" onClick={goBack} style={{ marginLeft: '1rem' }}>
            BACK TO DASHBOARD
          </button>
        </div>
      </div>

      {connectionError && (
        <div className="connection-error">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{connectionError}</span>
        </div>
      )}

      <div className="inventory-content">
        <div className="inventory-list-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 className="section-title">INVENTORY ITEMS</h2>
            <button className="control-btn" onClick={() => setShowCreateModal(true)}>
              + ADD ITEM
            </button>
          </div>
          <div className="inventory-table-container">
            <table className="inventory-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Fruit Type</th>
                  <th>Quantity</th>
                  <th>Arrival Date</th>
                  <th>Original Price</th>
                  <th>Current Price</th>
                  <th>Discount %</th>
                  <th>Freshness</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {inventory.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="empty-cell">No inventory items</td>
                  </tr>
                ) : (
                  inventory.map(item => (
                    <tr key={item.id}>
                      <td>{item.id}</td>
                      <td 
                        className="fruit-type-cell" 
                        onClick={() => handleFruitTypeClick(item.fruit_type)}
                        style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        title="Click to view detection images"
                      >
                        {item.fruit_type}
                      </td>
                      <td className="quantity-cell">{item.quantity}</td>
                      <td>{item.arrival_date ? new Date(item.arrival_date).toLocaleDateString() : '-'}</td>
                      <td>${item.original_price.toFixed(2)}</td>
                      <td>${item.current_price.toFixed(2)}</td>
                      <td>{item.discount_percentage !== undefined ? `${item.discount_percentage.toFixed(1)}%` : '-'}</td>
                      <td>
                        {item.freshness ? (
                          <div>
                            <div>Score: {(item.freshness.freshness_score * 100).toFixed(1)}%</div>
                            <div style={{ fontSize: '0.85em', color: item.freshness.status === 'fresh' ? '#7ECA9C' : item.freshness.status === 'warning' ? '#FFA500' : item.freshness.status === 'critical' ? '#FF6B6B' : '#999' }}>
                              {item.freshness.status.toUpperCase()}
                            </div>
                          </div>
                        ) : '-'}
                      </td>
                      <td>
                        <button 
                          className="inventory-action-btn edit-btn" 
                          onClick={() => setEditingItem(item)}
                          style={{ marginRight: '0.5rem' }}
                        >
                          EDIT
                        </button>
                        <button 
                          className="inventory-action-btn delete-btn" 
                          onClick={() => handleDelete(item.id)}
                        >
                          DELETE
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="changes-log-section">
          <h2 className="section-title">QUANTITY CHANGES LOG</h2>
          <div className="changes-log-container">
            {quantityChanges.length === 0 ? (
              <div className="empty-log">No quantity changes yet</div>
            ) : (
              quantityChanges.map((change, index) => (
                <div key={index} className={`change-log-item ${change.change_type}`}>
                  <div className="change-log-header">
                    <span className="change-fruit-type">{change.fruit_type}</span>
                    <span className="change-timestamp">
                      {new Date(change.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="change-log-details">
                    <span className="change-delta">
                      {change.change_type === 'increase' ? '+' : ''}{change.delta}
                    </span>
                    <span className="change-quantities">
                      {change.old_quantity} → {change.new_quantity}
                    </span>
                    {change.freshness_score !== null && change.freshness_score !== undefined && (
                      <span className="change-freshness" style={{ marginLeft: '1rem', fontSize: '0.9em', color: '#7ECA9C' }}>
                        Freshness: {(change.freshness_score * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingItem) && (
        <InventoryModal
          item={editingItem}
          onClose={() => {
            setShowCreateModal(false);
            setEditingItem(null);
          }}
          onSave={(itemData) => {
            if (editingItem) {
              handleUpdate(editingItem.id, itemData);
            } else {
              handleCreate(itemData);
            }
          }}
        />
      )}

      {/* Image Modal */}
      {showImageModal && (
        <div className="modal-overlay" onClick={() => {
          setShowImageModal(false);
          setExpandedImage(null);
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '90vw', maxHeight: '90vh', overflow: 'auto' }}>
            <div className="modal-header">
              <h2>Detection Images: {selectedItemCategory?.toUpperCase()}</h2>
              <button className="modal-close" onClick={() => {
                setShowImageModal(false);
                setExpandedImage(null);
              }}>×</button>
            </div>
            <div className="modal-body">
              {loadingImages ? (
                <div style={{ padding: '3rem', textAlign: 'center', color: '#7ECA9C' }}>
                  <div style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Loading images and detecting blemishes...</div>
                  <div style={{ 
                    display: 'inline-block',
                    width: '40px',
                    height: '40px',
                    border: '3px solid rgba(126, 202, 156, 0.3)',
                    borderTopColor: '#7ECA9C',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                </div>
              ) : selectedItemImages.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#999' }}>
                  No detection images found for this category yet.
                  <br />
                  Images will appear here as fruits are detected by the camera.
                </div>
              ) : (
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
                  gap: '1rem',
                  padding: '1rem'
                }}>
                  {selectedItemImages.map((image: DetectionImage, idx: number) => (
                    <div 
                      key={idx} 
                      onClick={() => setExpandedImage(image)}
                      style={{ 
                        border: '1px solid #333', 
                        borderRadius: '4px',
                        overflow: 'hidden',
                        background: '#1a1a1a',
                        cursor: 'pointer',
                        transition: 'transform 0.2s, border-color 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                        e.currentTarget.style.borderColor = '#7ECA9C';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.borderColor = '#333';
                      }}
                    >
                      <img 
                        src={`${config.apiUrl}/${image.path}`}
                        alt={`${selectedItemCategory} detection ${idx + 1}`}
                        style={{ 
                          width: '100%', 
                          height: '200px', 
                          objectFit: 'cover',
                          display: 'block'
                        }}
                      />
                      <div style={{ padding: '0.5rem', fontSize: '0.85em' }}>
                        {image.metadata?.confidence && (
                          <div>Confidence: {(image.metadata.confidence * 100).toFixed(1)}%</div>
                        )}
                        {image.metadata?.freshness_score !== undefined && image.metadata.freshness_score !== null && (
                          <div>Freshness: {typeof image.metadata.freshness_score === 'number' && image.metadata.freshness_score <= 1 
                            ? (image.metadata.freshness_score * 100).toFixed(1) 
                            : image.metadata.freshness_score.toFixed(1)}%</div>
                        )}
                        {image.metadata?.blemishes && (
                          <div style={{ marginTop: '0.25rem' }}>
                            {image.metadata.blemishes.error ? (
                              <div style={{ color: '#ff6b6b', fontSize: '0.8em' }}>
                                Blemish detection error
                              </div>
                            ) : (
                              <div>
                                <div style={{ 
                                  color: (image.metadata.blemishes.count || 0) > 0 ? '#ff6b6b' : '#7ECA9C',
                                  fontWeight: 'bold'
                                }}>
                                  Blemishes: {image.metadata.blemishes.count || 0}
                                </div>
                                {image.metadata.blemishes.labels && image.metadata.blemishes.labels.length > 0 && (
                                  <div style={{ fontSize: '0.75em', color: '#999', marginTop: '0.25rem' }}>
                                    {image.metadata.blemishes.labels.slice(0, 3).join(', ')}
                                    {image.metadata.blemishes.labels.length > 3 && '...'}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                        <div style={{ fontSize: '0.75em', color: '#999', marginTop: '0.25rem' }}>
                          {new Date(image.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Expanded Image Modal with Blemish Annotations */}
      {expandedImage && (
        <div className="modal-overlay" onClick={() => setExpandedImage(null)} style={{ zIndex: 1001 }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ 
            maxWidth: '95vw', 
            maxHeight: '95vh', 
            overflow: 'auto',
            position: 'relative'
          }}>
            <div className="modal-header">
              <h2>Blemish Detection: {selectedItemCategory?.toUpperCase()}</h2>
              <button className="modal-close" onClick={() => setExpandedImage(null)}>×</button>
            </div>
            <div className="modal-body" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ position: 'relative', maxWidth: '100%', marginBottom: '1rem' }}>
                <img 
                  id={`expanded-image-${expandedImage.filename}`}
                  src={`${config.apiUrl}/${expandedImage.path}`}
                  alt="Expanded detection"
                  crossOrigin="anonymous"
                  style={{ 
                    maxWidth: '100%',
                    maxHeight: '70vh',
                    display: 'block',
                    margin: '0 auto'
                  }}
                  onLoad={(e) => {
                    // Draw blemish bounding boxes on the image
                    const img = e.currentTarget;
                    
                    // Skip if this is already a canvas data URL (to prevent infinite loop)
                    if (img.src.startsWith('data:')) {
                      return;
                    }
                    
                    // Wait for image to be fully loaded with dimensions
                    if (img.naturalWidth > 0 && img.naturalHeight > 0) {
                      const canvas = document.createElement('canvas');
                      canvas.width = img.naturalWidth;
                      canvas.height = img.naturalHeight;
                      const ctx = canvas.getContext('2d');
                      
                      if (!ctx) {
                        console.error('Failed to get canvas context');
                        return;
                      }
                      
                      if (!expandedImage.metadata?.blemishes?.bboxes || expandedImage.metadata.blemishes.bboxes.length === 0) {
                        console.log('No blemishes to draw');
                        return;
                      }
                      
                      // Draw the image on canvas
                      ctx.drawImage(img, 0, 0);
                      
                      console.log(`Drawing ${expandedImage.metadata.blemishes.bboxes.length} blemishes on image ${img.naturalWidth}x${img.naturalHeight}`);
                      
                      // Draw bounding boxes for blemishes
                      expandedImage.metadata.blemishes.bboxes.forEach((bbox: any, idx: number) => {
                        if (!bbox.box_2d || !Array.isArray(bbox.box_2d) || bbox.box_2d.length !== 4) {
                          console.warn('Invalid bbox format:', bbox);
                          return;
                        }
                        
                        const [ymin, xmin, ymax, xmax] = bbox.box_2d;
                        const label = bbox.label || expandedImage.metadata?.blemishes?.labels?.[idx] || 'blemish';
                        
                        // Convert normalized coordinates (0-1000) to pixel coordinates
                        const x1 = (xmin / 1000) * img.naturalWidth;
                        const y1 = (ymin / 1000) * img.naturalHeight;
                        const x2 = (xmax / 1000) * img.naturalWidth;
                        const y2 = (ymax / 1000) * img.naturalHeight;
                        const width = x2 - x1;
                        const height = y2 - y1;
                        
                        console.log(`Blemish ${idx + 1}: [${xmin}, ${ymin}, ${xmax}, ${ymax}] -> [${x1.toFixed(1)}, ${y1.toFixed(1)}, ${x2.toFixed(1)}, ${y2.toFixed(1)}] (${width.toFixed(1)}x${height.toFixed(1)})`);
                        
                        // Only draw if coordinates are valid
                        if (width > 0 && height > 0) {
                          // Draw bounding box
                          ctx.strokeStyle = '#ff6b6b';
                          ctx.lineWidth = 3;
                          ctx.strokeRect(x1, y1, width, height);
                          
                          // Draw label background
                          ctx.fillStyle = 'rgba(255, 107, 107, 0.8)';
                          ctx.font = 'bold 16px "Geist Mono", monospace';
                          const textMetrics = ctx.measureText(label);
                          const textWidth = textMetrics.width;
                          const textHeight = 20;
                          const labelY = Math.max(textHeight + 4, y1);
                          ctx.fillRect(x1, labelY - textHeight - 4, textWidth + 8, textHeight);
                          
                          // Draw label text
                          ctx.fillStyle = '#ffffff';
                          ctx.fillText(label, x1 + 4, labelY - 8);
                        } else {
                          console.warn(`Invalid dimensions for blemish ${idx + 1}: ${width}x${height}`);
                        }
                      });
                      
                      // Replace img src with canvas data URL
                      img.src = canvas.toDataURL();
                      console.log('Canvas drawn and applied to image');
                    } else {
                      console.warn('Image not fully loaded:', { naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight });
                    }
                  }}
                />
              </div>
              <div style={{ 
                width: '100%', 
                padding: '1rem', 
                background: '#1a1a1a', 
                borderRadius: '4px',
                border: '1px solid #333'
              }}>
                <h3 style={{ marginTop: 0, marginBottom: '0.5rem', color: '#7ECA9C' }}>Image Details</h3>
                {expandedImage.metadata?.confidence && (
                  <div style={{ marginBottom: '0.5rem' }}>
                    <strong>Confidence:</strong> {(expandedImage.metadata.confidence * 100).toFixed(1)}%
                  </div>
                )}
                {expandedImage.metadata?.freshness_score !== undefined && expandedImage.metadata.freshness_score !== null && (
                  <div style={{ marginBottom: '0.5rem' }}>
                    <strong>Freshness:</strong> {typeof expandedImage.metadata.freshness_score === 'number' && expandedImage.metadata.freshness_score <= 1 
                      ? (expandedImage.metadata.freshness_score * 100).toFixed(1) 
                      : expandedImage.metadata.freshness_score.toFixed(1)}%
                  </div>
                )}
                {expandedImage.metadata?.blemishes && (
                  <div style={{ marginTop: '1rem' }}>
                    {expandedImage.metadata.blemishes.error ? (
                      <div style={{ color: '#ff6b6b' }}>
                        <strong>Blemish Detection Error:</strong> {expandedImage.metadata.blemishes.error}
                      </div>
                    ) : (
                      <>
                        <div style={{ 
                          marginBottom: '0.5rem',
                          color: (expandedImage.metadata.blemishes.count || 0) > 0 ? '#ff6b6b' : '#7ECA9C',
                          fontWeight: 'bold',
                          fontSize: '1.1em'
                        }}>
                          Blemishes Detected: {expandedImage.metadata.blemishes.count || 0}
                        </div>
                        {expandedImage.metadata.blemishes.bboxes && expandedImage.metadata.blemishes.bboxes.length > 0 && (
                          <div style={{ marginTop: '0.5rem' }}>
                            <strong>Blemish Details:</strong>
                            <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                              {expandedImage.metadata?.blemishes?.bboxes?.map((bbox: any, idx: number) => (
                                <li key={idx} style={{ marginBottom: '0.25rem' }}>
                                  <span style={{ color: '#ff6b6b' }}>{bbox.label || expandedImage.metadata?.blemishes?.labels?.[idx] || 'Blemish'}</span>
                                  {' '}(Box: [{bbox.box_2d[0]}, {bbox.box_2d[1]}, {bbox.box_2d[2]}, {bbox.box_2d[3]}])
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {expandedImage.metadata.blemishes.labels && expandedImage.metadata.blemishes.labels.length > 0 && (
                          <div style={{ marginTop: '0.5rem' }}>
                            <strong>Labels:</strong> {expandedImage.metadata.blemishes.labels.join(', ')}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
                <div style={{ marginTop: '1rem', fontSize: '0.9em', color: '#999' }}>
                  <strong>Timestamp:</strong> {new Date(expandedImage.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface InventoryModalProps {
  item: InventoryItem | null;
  onClose: () => void;
  onSave: (itemData: Partial<InventoryItem>) => void;
}

const InventoryModal = ({ item, onClose, onSave }: InventoryModalProps) => {
  const [formData, setFormData] = useState<Partial<InventoryItem>>({
    fruit_type: item?.fruit_type || '',
    variety: item?.variety || '',
    quantity: item?.quantity || 0,
    batch_number: item?.batch_number || '',
    location_in_store: item?.location_in_store || '',
    original_price: item?.original_price || 0,
    current_price: item?.current_price || item?.original_price || 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...formData,
      quantity: Number(formData.quantity) || 0,
      original_price: Number(formData.original_price) || 0,
      current_price: Number(formData.current_price) || 0,
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{item ? 'EDIT ITEM' : 'CREATE ITEM'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit} className="inventory-form">
          <div className="form-row">
            <div className="form-group">
              <label>Fruit Type *</label>
              <input
                type="text"
                value={formData.fruit_type}
                onChange={(e) => setFormData({ ...formData, fruit_type: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Variety</label>
              <input
                type="text"
                value={formData.variety}
                onChange={(e) => setFormData({ ...formData, variety: e.target.value })}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Quantity *</label>
              <input
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
                required
                min="0"
              />
            </div>
            <div className="form-group">
              <label>Batch Number</label>
              <input
                type="text"
                value={formData.batch_number}
                onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Location</label>
              <input
                type="text"
                value={formData.location_in_store}
                onChange={(e) => setFormData({ ...formData, location_in_store: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Original Price *</label>
              <input
                type="number"
                step="0.01"
                value={formData.original_price}
                onChange={(e) => setFormData({ ...formData, original_price: parseFloat(e.target.value) || 0 })}
                required
                min="0"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Current Price *</label>
              <input
                type="number"
                step="0.01"
                value={formData.current_price}
                onChange={(e) => setFormData({ ...formData, current_price: parseFloat(e.target.value) || 0 })}
                required
                min="0"
              />
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="control-btn" onClick={onClose}>
              CANCEL
            </button>
            <button type="submit" className="control-btn" style={{ marginLeft: '1rem' }}>
              {item ? 'UPDATE' : 'CREATE'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InventoryView;

