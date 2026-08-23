import React, { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';

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
    visibility: initialData?.visibility || 'EVERYONE',
    dept_id_list: initialData?.departments ? initialData.departments.map((d: any) => typeof d === 'object' ? d.id : d) : []
  });
  const [error, setError] = useState('');
  const [departments, setDepartments] = useState<any[]>([]);

  useEffect(() => {
    apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/departments`)
      .then(d => setDepartments(d))
      .catch(e => console.error(e));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    const endpoint = isEditing 
      ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resources/${initialData.id}` 
      : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resources`;
      
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

  const toggleDept = (id: number) => {
    setFormData(prev => ({
      ...prev,
      dept_id_list: prev.dept_id_list.includes(id) 
        ? prev.dept_id_list.filter((x: number) => x !== id)
        : [...prev.dept_id_list, id]
    }));
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
          
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Visibility</label>
            <div style={{ display: 'flex', gap: '16px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input type="radio" name="visibility" value="EVERYONE" checked={formData.visibility === 'EVERYONE'} onChange={e => setFormData({...formData, visibility: e.target.value})} />
                Everyone
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input type="radio" name="visibility" value="ADMIN_ONLY" checked={formData.visibility === 'ADMIN_ONLY'} onChange={e => setFormData({...formData, visibility: e.target.value})} />
                Admin Only
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input type="radio" name="visibility" value="SELECTED_DEPARTMENTS" checked={formData.visibility === 'SELECTED_DEPARTMENTS'} onChange={e => setFormData({...formData, visibility: e.target.value})} />
                Selected Departments
              </label>
            </div>
          </div>

          {formData.visibility === 'SELECTED_DEPARTMENTS' && (
            <div>
              <label style={{ display: 'block', marginBottom: '8px' }}>Select Departments</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '150px', overflowY: 'auto', border: '1px solid rgba(255,255,255,0.1)', padding: '8px' }}>
                {departments.map(d => (
                  <label key={d.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input type="checkbox" checked={formData.dept_id_list.includes(d.id)} onChange={() => toggleDept(d.id)} />
                    {d.name}
                  </label>
                ))}
              </div>
            </div>
          )}
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}
