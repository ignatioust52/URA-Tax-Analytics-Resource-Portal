import React, { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Input } from './ui/Input';

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
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
      <Card style={{ width: '100%', maxWidth: '600px', padding: 'var(--space-5)', boxShadow: 'var(--shadow-lg)', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-4)' }}>{isEditing ? 'Edit Resource' : 'Add Resource'}</h2>
        {error && <div style={{ color: 'var(--error)', marginBottom: 'var(--space-3)' }}>{error}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
          <Input 
            label="Page Name"
            type="text" 
            required 
            value={formData.page_name} 
            onChange={e => setFormData({...formData, page_name: e.target.value})} 
          />
          <Input 
            label="Business Name"
            type="text" 
            required 
            value={formData.business_name} 
            onChange={e => setFormData({...formData, business_name: e.target.value})} 
          />
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <label>Description</label>
            <textarea 
              value={formData.description} 
              onChange={e => setFormData({...formData, description: e.target.value})} 
              rows={3}
              style={{ 
                width: '100%', 
                padding: '10px 12px', 
                borderRadius: 'var(--radius-md)', 
                border: '1px solid var(--border-medium)', 
                background: 'var(--surface)', 
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                outline: 'none',
                resize: 'vertical'
              }} 
            />
          </div>
          <Input 
            label="Category"
            type="text" 
            value={formData.category} 
            onChange={e => setFormData({...formData, category: e.target.value})} 
          />
          <Input 
            label="URL"
            type="url" 
            required 
            value={formData.url} 
            onChange={e => setFormData({...formData, url: e.target.value})} 
          />
          
          <div style={{ marginBottom: 'var(--space-3)' }}>
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
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Select Departments</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '150px', overflowY: 'auto', border: '1px solid var(--border-medium)', padding: '8px', borderRadius: 'var(--radius-md)' }}>
                {departments.map(d => (
                  <label key={d.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input type="checkbox" checked={formData.dept_id_list.includes(d.id)} onChange={() => toggleDept(d.id)} />
                    {d.name}
                  </label>
                ))}
              </div>
            </div>
          )}
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: 'var(--space-5)' }}>
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit">Save Resource</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
