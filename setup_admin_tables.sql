CREATE TABLE IF NOT EXISTS public_resources (
    id SERIAL PRIMARY KEY,
    page TEXT NOT NULL,
    business TEXT NOT NULL,
    description TEXT,
    category TEXT,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO public_resources (page, business, description, category, url)
VALUES (
    'URA Power BI Report',
    'Uganda Revenue Authority',
    'Embedded Power BI dashboard for revenue and customs reporting.',
    'URA',
    ''
);

CREATE TABLE IF NOT EXISTS resource_reviews (
    id SERIAL PRIMARY KEY,
    page TEXT NOT NULL,
    reviewer TEXT,
    rating INTEGER NOT NULL,
    comment TEXT,
    submitted_at TIMESTAMP DEFAULT NOW()
);
