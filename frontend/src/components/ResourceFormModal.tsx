import React, { useState } from 'react';

export function ResourceFormModal({ 
  onClose, 
  onSuccess, 
  initialData 
}: { 
  onClose: () => void, 
  onSuccess: () => void, 
  initialData?: any 
}) {
  const isEditing = !!initialData;
  const [formData, setFormData] = useState({
    page_name: initialData?.page_name || '',
    business_name: initialData?.business_name || '',
    description: initialData?.description || '',
    category: initialData?.category || '',
    url: initialData?.url || '',
    admin_only: initialData?.admin_only || false,
    dept_id_list: []
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    const endpoint = isEditing 
      ? `http://localhost:8000/api/resources/${initialData.id}` 
      : `http://localhost:8000/api/resources`;
      
    const method = isEditing ? 'PUT' : 'POST';

    try {
      const res = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });
      if (!res.ok) {
        const d = await res.json();
        setError(d.detail || 'Save failed');
        return;
      }
      onSuccess();
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '600px', padding: '32px', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ marginBottom: '24px' }}>{isEditing ? 'Edit Resource' : 'Add Resource'}</h2>
        {error && <div style={{ color: '#ef4444', marginBottom: '16px' }}>{error}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Page Name</label>
            <input required type="text" value={formData.page_name} onChange={e => setFormData({...formData, page_name: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Business Name</label>
            <input required type="text" value={formData.business_name} onChange={e => setFormData({...formData, business_name: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Description</label>
            <textarea value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Category</label>
            <input type="text" value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>URL</label>
            <input required type="url" value={formData.url} onChange={e => setFormData({...formData, url: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input type="checkbox" checked={formData.admin_only} onChange={e => setFormData({...formData, admin_only: e.target.checked})} />
            <label>Admin Only</label>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}
