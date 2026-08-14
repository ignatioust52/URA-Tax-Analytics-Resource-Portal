import textwrap

# Append login CSS to assets/style.css
css_rules = """
/* --- LOGIN PAGE SPLIT STYLES --- */
.login-left-pane {
    background: linear-gradient(145deg, #1B367A 0%, #243F8D 60%, #15295C 100%);
    width: 100%;
    min-height: 85vh;
    border-radius: 16px;
    padding: 3rem 4rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.login-left-header {
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 2;
}

.login-brand-title {
    color: #FFFFFF;
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    line-height: 1.2;
}
.login-brand-title span {
    color: #FFF200;
}
.login-brand-subtitle {
    color: rgba(255, 255, 255, 0.75);
    font-size: 0.8rem;
    font-weight: 400;
}

.login-illustration-container {
    position: relative;
    width: 320px;
    height: 380px;
    margin: 2rem auto;
    z-index: 2;
}

.login-doc-card {
    width: 240px;
    height: 310px;
    background: #FFFFFF;
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.25);
    position: absolute;
    left: 20px;
    top: 40px;
    padding: 24px 20px;
    overflow: hidden;
}
.login-doc-top-bar {
    height: 12px;
    background: #FFF200;
    border-radius: 6px;
    margin-bottom: 20px;
}
.login-doc-line {
    height: 8px;
    background: #4C74B2;
    opacity: 0.4;
    border-radius: 4px;
    margin-bottom: 10px;
}
.login-doc-line.short { width: 50%; }
.login-doc-line.medium { width: 75%; }
.login-doc-line.long { width: 100%; }

.login-doc-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 16px;
}
.login-doc-icon {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    color: white;
}
.login-doc-icon.green { background: #008751; }
.login-doc-icon.orange { background: #F97316; }
.login-doc-icon.gray { background: #CBD5E1; }
.login-doc-pill {
    height: 8px;
    background: #EDEFF6;
    border-radius: 4px;
    flex-grow: 1;
}

.login-doc-bottom-pill {
    height: 12px;
    background: #243F8D;
    border-radius: 6px;
    width: 70px;
    margin-top: 24px;
}

.login-badge-top-right {
    position: absolute;
    top: 10px;
    right: 15px;
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: #FFF200;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 16px rgba(0,0,0,0.15);
}
.login-badge-top-right-inner {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #243F8D;
    font-size: 24px;
    font-weight: bold;
}
.login-badge-plus {
    position: absolute;
    right: 0px;
    top: 190px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.4);
    background: rgba(36, 63, 141, 0.6);
    backdrop-filter: blur(4px);
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}
.login-badge-bottom-right {
    position: absolute;
    bottom: 0px;
    right: 50px;
    width: 62px;
    height: 62px;
    border-radius: 50%;
    background: #008751;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    font-weight: bold;
    box-shadow: 0 10px 20px rgba(0,135,81,0.3);
    border: 4px solid #FFFFFF;
}

.bg-circle-1 {
    position: absolute;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 70%);
    top: -150px;
    right: -150px;
    pointer-events: none;
}
.bg-circle-2 {
    position: absolute;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,242,0,0.04) 0%, rgba(255,242,0,0) 70%);
    bottom: -200px;
    left: -200px;
    pointer-events: none;
}

.login-card-header {
    text-align: center;
    margin-bottom: 1.5rem;
}
.login-card-header-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #243F8D;
    margin-top: 10px;
    letter-spacing: 0.5px;
}
.login-card-header-title span {
    color: #7F7801;
}
.login-card-header-sub {
    color: #636363;
    font-size: 0.85rem;
}
"""

with open("assets/style.css", "a") as f:
    f.write("\n" + css_rules)

print("CSS appended to assets/style.css")
