"use client";
import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ResourceFormModal } from '../../components/ResourceFormModal';
import { apiFetch } from '../../lib/api';

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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: userMsg })
      });
      if (res.ok) {
        const data = await res.json();
        setChatHistory(prev => [...prev, { role: 'assistant', content: data.reply }]);
        setAiFilters(data.filters);
      }
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
    // Fetch all initial data concurrently
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

  const handleResourceClick = (res: Resource) => {
    setSelectedResource(res);
    // Optionally trigger an API call to record view
  };

  const [showModal, setShowModal] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);

  const reloadData = () => {
    setLoading(true);
    Promise.all([
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resources`, { credentials: 'include' }).then(r => r.ok ? r.json() : []),
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resources/favorites`, { credentials: 'include' }).then(r => r.ok ? r.json() : []),
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resources/recent`, { credentials: 'include' }).then(r => r.ok ? r.json() : []),
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/announcements/active`, { credentials: 'include' }).then(r => r.ok ? r.json() : []),
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h1 className="header-title" style={{ fontSize: '1.75rem', marginBottom: '8px' }}>{selectedResource.business_name}</h1>
            <p className="header-subtitle" style={{ margin: 0 }}>
              {selectedResource.category || 'General'} • Added {new Date(selectedResource.created_at).toLocaleDateString()}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-secondary" onClick={() => {}}>⭐ Favorite</button>
            <button className="btn-secondary" onClick={() => setSelectedResource(null)}>← Back to grid</button>
          </div>
        </div>
        
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden', height: 'calc(100vh - 200px)' }}>
          {selectedResource.url.includes('youtube') || selectedResource.url.includes('youtu.be') ? (
            <iframe width="100%" height="100%" src={selectedResource.url.replace("watch?v=", "embed/")} frameBorder="0" allowFullScreen></iframe>
          ) : (
            <iframe width="100%" height="100%" src={selectedResource.url} frameBorder="0" allowFullScreen></iframe>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="main-container">
      {/* Header and Search/Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <h1 className="header-title" style={{ fontSize: '2rem' }}>Public Resources</h1>
          <p className="header-subtitle" style={{ marginBottom: 0 }}>Explore URA reports, guides, and documentation</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexGrow: 1, maxWidth: '600px', alignItems: 'center' }}>
          <input 
            type="text" 
            placeholder="Search resources..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ flexGrow: 1, padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
          />
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          {user && (
            <button onClick={() => { setEditingResource(null); setShowModal(true); }} className="btn-primary" style={{ padding: '10px 16px', whiteSpace: 'nowrap' }}>
              + Add Resource
            </button>
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
      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid var(--border)', marginBottom: '24px' }}>
        {['all', 'favorites', 'recent', 'news', 'ai'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'none', border: 'none', padding: '12px 4px', cursor: 'pointer',
              color: activeTab === tab ? 'white' : 'var(--text-secondary)',
              borderBottom: activeTab === tab ? '2px solid var(--accent)' : '2px solid transparent',
              fontWeight: activeTab === tab ? 600 : 400,
              textTransform: 'capitalize'
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
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>Loading...</div>
      ) : activeTab === 'news' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {announcements.length === 0 ? (
            <div className="glass-panel" style={{ textAlign: 'center' }}>No active announcements.</div>
          ) : announcements.map(ann => (
            <div key={ann.id} className="glass-panel">
              <h3 style={{ marginBottom: '8px' }}>📢 {ann.title}</h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                Published on {new Date(ann.published_at).toLocaleString()}
              </div>
              <p>{ann.body}</p>
            </div>
          ))}
        </div>
      ) : activeTab === 'ai' ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
            <h3>URA AI Assistant</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '16px' }}>
              Ask me to find specific dashboards, e.g., 'Show VAT collections in Kampala'.
            </p>
            <div style={{ flexGrow: 1, overflowY: 'auto', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {chatHistory.map((msg, idx) => (
                <div key={idx} style={{ 
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  background: msg.role === 'user' ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                  padding: '10px 14px', borderRadius: '12px', maxWidth: '85%', fontSize: '0.95rem'
                }}>
                  {msg.content}
                </div>
              ))}
            </div>
            <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask for a dashboard..." 
                style={{ flexGrow: 1, padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
              />
              <button type="submit" className="btn-primary" style={{ padding: '0 16px' }}>Send</button>
            </form>
          </div>
          <div>
            <h3 style={{ marginBottom: '16px' }}>AI Recommended Results</h3>
            {aiFilters && getFilteredAiResources().length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
                {getFilteredAiResources().map((resource) => (
                  <div key={resource.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                        {resource.category || 'General'}
                      </div>
                    </div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', fontWeight: 600 }}>
                      {resource.page_name || resource.business_name}
                    </h3>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                      <button onClick={() => handleResourceClick(resource)} className="btn-primary" style={{ padding: '6px 16px', fontSize: '0.9rem' }}>
                        View Resource
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : aiFilters ? (
              <div className="glass-panel" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No dashboards found matching your criteria.</div>
            ) : (
              <div className="glass-panel" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Start chatting to see recommended dashboards.</div>
            )}
          </div>
        </div>
      ) : getDisplayedResources().length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center' }}>No resources match your filters.</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          {getDisplayedResources().map((resource) => (
            <div key={resource.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                  {resource.category || 'General'}
                </div>
                <span className="ura-chip ura-chip-green">Available</span>
              </div>
              
              <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', fontWeight: 600 }}>
                {resource.page_name || resource.business_name}
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', flexGrow: 1, lineHeight: 1.5 }}>
                {resource.description || 'No description provided.'}
              </p>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>👁 {resource.view_count || 0} views</span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {user?.role === 'admin' && (
                    <button onClick={() => { setEditingResource(resource); setShowModal(true); }} className="btn-secondary" style={{ padding: '6px 16px', fontSize: '0.9rem' }}>
                      Edit
                    </button>
                  )}
                  <button onClick={() => handleResourceClick(resource)} className="btn-primary" style={{ padding: '6px 16px', fontSize: '0.9rem' }}>
                    View Resource
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
