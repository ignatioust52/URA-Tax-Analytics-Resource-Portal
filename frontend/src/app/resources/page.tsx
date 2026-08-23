"use client";
import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ResourceFormModal } from '../../components/ResourceFormModal';
import { apiFetch } from '../../lib/api';
import { Card, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';

type Resource = {
  id: number;
  page_name: string;
  business_name: string;
  description: string;
  category: string;
  url: string;
  department: string;
  created_at: string;
  view_count: number;
};

type Announcement = {
  id: number;
  title: string;
  body: string;
  published_at: string;
};

export default function ResourcesPage() {
  const { user } = useAuth();
  const [resources, setResources] = useState<Resource[]>([]);
  const [favorites, setFavorites] = useState<Resource[]>([]);
  const [recent, setRecent] = useState<Resource[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [activeTab, setActiveTab] = useState('all'); // all, favorites, recent, news, ai
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);

  // AI Chat states
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: string, content: string}[]>([
    { role: 'assistant', content: 'Hello! I am your URA AI Assistant. Tell me what kind of dashboard you are looking for.' }
  ]);
  const [aiFilters, setAiFilters] = useState<{region: string, tax_type: string} | null>(null);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    
    try {
      const data = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      setChatHistory(prev => [...prev, { role: 'assistant', content: data.reply }]);
      setAiFilters(data.filters);
    } catch (err) {
      console.error(err);
    }
  };

  const getFilteredAiResources = () => {
    if (!aiFilters) return [];
    return resources.filter(r => {
      const text = `${r.business_name} ${r.category}`.toLowerCase();
      const matchRegion = aiFilters.region && text.includes(aiFilters.region.toLowerCase());
      const matchTax = aiFilters.tax_type && text.includes(aiFilters.tax_type.toLowerCase());
      
      if (aiFilters.region && aiFilters.tax_type) return matchRegion && matchTax;
      if (aiFilters.region) return matchRegion || text.includes('revenue');
      if (aiFilters.tax_type) return matchTax;
      return true;
    });
  };

  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    Promise.all([
      apiFetch(`${baseUrl}/api/resources`).catch(() => []),
      apiFetch(`${baseUrl}/api/resources/favorites`).catch(() => []),
      apiFetch(`${baseUrl}/api/resources/recent`).catch(() => []),
      apiFetch(`${baseUrl}/api/announcements/active`).catch(() => []),
    ]).then(([resData, favData, recentData, annData]) => {
      setResources(resData || []);
      setFavorites(favData || []);
      setRecent(recentData || []);
      setAnnouncements(annData || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const categories = ['All', ...Array.from(new Set(resources.map(r => r.category || 'General')))];

  const getDisplayedResources = () => {
    let base = resources;
    if (activeTab === 'favorites') base = favorites;
    if (activeTab === 'recent') base = recent;

    return base.filter(r => {
      const matchSearch = (r.page_name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
                           r.business_name?.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchCategory = selectedCategory === 'All' || r.category === selectedCategory || (!r.category && selectedCategory === 'General');
      return matchSearch && matchCategory;
    });
  };

  const handleResourceClick = async (res: Resource) => {
    setSelectedResource(res);
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resources/${res.id}/view`, { method: 'POST' });
    } catch (err) {
      console.error('Failed to log view:', err);
    }
  };

  const [showModal, setShowModal] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);

  const reloadData = () => {
    setLoading(true);
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    Promise.all([
      apiFetch(`${baseUrl}/api/resources`).catch(() => []),
      apiFetch(`${baseUrl}/api/resources/favorites`).catch(() => []),
      apiFetch(`${baseUrl}/api/resources/recent`).catch(() => []),
      apiFetch(`${baseUrl}/api/announcements/active`).catch(() => []),
    ]).then(([resData, favData, recentData, annData]) => {
      setResources(resData || []);
      setFavorites(favData || []);
      setRecent(recentData || []);
      setAnnouncements(annData || []);
      setLoading(false);
    });
  };

  if (selectedResource) {
    return (
      <main className="main-container">
        <div className="flex-between" style={{ marginBottom: 'var(--space-4)' }}>
          <div>
            <h1 className="page-title" style={{ margin: 0, fontSize: '1.75rem' }}>{selectedResource.business_name}</h1>
            <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>
              {selectedResource.category || 'General'} • Added {new Date(selectedResource.created_at).toLocaleDateString()}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="secondary" onClick={() => {}}>⭐ Favorite</Button>
            <Button variant="secondary" onClick={() => setSelectedResource(null)}>← Back to grid</Button>
          </div>
        </div>
        
        <Card noPadding style={{ height: 'calc(100vh - 200px)' }}>
          {selectedResource.url.includes('youtube') || selectedResource.url.includes('youtu.be') ? (
            <iframe width="100%" height="100%" src={selectedResource.url.replace("watch?v=", "embed/")} frameBorder="0" allowFullScreen></iframe>
          ) : (
            <iframe width="100%" height="100%" src={selectedResource.url} frameBorder="0" allowFullScreen></iframe>
          )}
        </Card>
      </main>
    );
  }

  return (
    <main className="main-container">
      {/* Header and Search/Filter Bar */}
      <div className="flex-between" style={{ marginBottom: 'var(--space-5)', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>Public Resources</h1>
          <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>Explore URA reports, guides, and documentation</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexGrow: 1, maxWidth: '600px', alignItems: 'center' }}>
          <Input 
            placeholder="Search resources..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ marginBottom: 0 }}
          />
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ 
              padding: '10px 16px', 
              borderRadius: 'var(--radius-md)', 
              border: '1px solid var(--border-medium)', 
              background: 'var(--surface)', 
              color: 'var(--text-primary)',
              height: '42px',
              outline: 'none'
            }}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          {user?.role && (user.role.includes('admin') || user.role === 'manager') && (
            <Button onClick={() => { setEditingResource(null); setShowModal(true); }} style={{ whiteSpace: 'nowrap', height: '42px' }}>
              + Add Resource
            </Button>
          )}
        </div>
      </div>

      {showModal && (
        <ResourceFormModal 
          initialData={editingResource}
          onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); reloadData(); }}
        />
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 'var(--space-4)', borderBottom: '1px solid var(--border-light)', marginBottom: 'var(--space-4)', overflowX: 'auto', whiteSpace: 'nowrap', paddingBottom: '4px' }}>
        {['all', 'favorites', 'recent', 'news', 'ai'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'none', 
              border: 'none', 
              padding: 'var(--space-3) var(--space-1)', 
              cursor: 'pointer',
              color: activeTab === tab ? 'var(--ura-blue)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab ? '2px solid var(--ura-blue)' : '2px solid transparent',
              fontWeight: activeTab === tab ? 600 : 500,
              textTransform: 'capitalize',
              fontSize: '0.95rem'
            }}
          >
            {tab === 'all' ? 'All Resources' : 
             tab === 'favorites' ? 'My Favorites' : 
             tab === 'recent' ? 'Recently Viewed' : 
             tab === 'news' ? 'News Feed' : 'AI Assistant'}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-secondary)' }}>Loading...</div>
      ) : activeTab === 'news' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {announcements.length === 0 ? (
            <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No active announcements.</Card>
          ) : announcements.map(ann => (
            <Card key={ann.id}>
              <h3 style={{ marginBottom: 'var(--space-2)' }}>📢 {ann.title}</h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', marginBottom: 'var(--space-4)' }}>
                Published on {new Date(ann.published_at).toLocaleString()}
              </div>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{ann.body}</p>
            </Card>
          ))}
        </div>
      ) : activeTab === 'ai' ? (
        <div className="grid-dashboard">
          <Card style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
            <h3 style={{ marginBottom: 'var(--space-2)' }}>URA AI Assistant</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 'var(--space-4)' }}>
              Ask me to find specific dashboards, e.g., 'Show VAT collections in Kampala'.
            </p>
            <div style={{ flexGrow: 1, overflowY: 'auto', marginBottom: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {chatHistory.map((msg, idx) => (
                <div key={idx} style={{ 
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  background: msg.role === 'user' ? 'var(--ura-blue)' : 'var(--surface-hover)',
                  color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                  padding: '10px 14px', 
                  borderRadius: 'var(--radius-lg)', 
                  maxWidth: '85%', 
                  fontSize: '0.95rem'
                }}>
                  {msg.content}
                </div>
              ))}
            </div>
            <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '8px' }}>
              <Input 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask for a dashboard..." 
                fullWidth
                style={{ marginBottom: 0 }}
              />
              <Button type="submit">Send</Button>
            </form>
          </Card>
          
          <div>
            <h3 style={{ marginBottom: 'var(--space-4)' }}>AI Recommended Results</h3>
            {aiFilters && getFilteredAiResources().length > 0 ? (
              <div className="grid-cards">
                {getFilteredAiResources().map((resource) => (
                  <Card key={resource.id} style={{ display: 'flex', flexDirection: 'column' }}>
                    <div className="flex-between" style={{ marginBottom: 'var(--space-2)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--ura-blue)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                        {resource.category || 'General'}
                      </div>
                    </div>
                    <h3 style={{ fontSize: '1.125rem', marginBottom: 'var(--space-2)' }}>
                      {resource.page_name || resource.business_name}
                    </h3>
                    <div className="flex-between" style={{ marginTop: 'auto', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--border-light)' }}>
                      <Button onClick={() => handleResourceClick(resource)} size="sm">
                        View Resource
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            ) : aiFilters ? (
              <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No dashboards found matching your criteria.</Card>
            ) : (
              <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Start chatting to see recommended dashboards.</Card>
            )}
          </div>
        </div>
      ) : getDisplayedResources().length === 0 ? (
        <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '2rem', marginBottom: 'var(--space-2)' }}>📊</div>
          <h3>No resources found</h3>
          <p>Try adjusting your search or filters.</p>
        </Card>
      ) : (
        <div className="grid-cards">
          {getDisplayedResources().map((resource) => (
            <Card key={resource.id} style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="flex-between" style={{ marginBottom: 'var(--space-2)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--ura-blue)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                  {resource.category || 'General'}
                </div>
                <Badge variant="success">Available</Badge>
              </div>
              
              <h3 style={{ fontSize: '1.25rem', marginBottom: 'var(--space-2)' }}>
                {resource.page_name || resource.business_name}
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 'var(--space-5)', flexGrow: 1, lineHeight: 1.5 }}>
                {resource.description || 'No description provided.'}
              </p>
              
              <div className="flex-between" style={{ marginTop: 'auto', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--border-light)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', fontWeight: 500 }}>
                  👁 {resource.view_count || 0} views
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {user?.role && (user.role.includes('admin') || user.role === 'manager') && (
                    <Button variant="secondary" size="sm" onClick={() => { setEditingResource(resource); setShowModal(true); }}>
                      Edit
                    </Button>
                  )}
                  <Button size="sm" onClick={() => handleResourceClick(resource)}>
                    View Resource
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}
