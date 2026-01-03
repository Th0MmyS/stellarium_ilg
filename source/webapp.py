import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import math

st.set_page_config(page_title="Astro-Horizon Precision Tool", layout="wide")

# --- Initialize Session State ---
if "points" not in st.session_state:
    st.session_state.points = []
if "last_click" not in st.session_state:
    st.session_state.last_click = None

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# Zoom Factor (1.1x)
PADDING = 1.1 

@st.cache_data
def get_zoomed_polar(file_bytes, padding):
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    size = 800 
    center = size // 2
    visual_horizon_r = center / padding 
    
    y_grid, x_grid = np.indices((size, size), dtype=np.float32)
    dx, dy = x_grid - center, y_grid - center
    r = np.sqrt(dx**2 + dy**2)
    
    # Projection Math
    theta_img = np.arctan2(dx, dy) 
    ux = ((theta_img + np.pi) % (2 * np.pi)) * (w / (2 * np.pi))
    vy = (r / visual_horizon_r) * (h / 2.0)
    
    polar = cv2.remap(img, ux, vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    return cv2.cvtColor(polar, cv2.COLOR_BGR2RGB), center, visual_horizon_r

st.title("🌌 Astro-Horizon Precision Tool")

col_map, col_data = st.columns([2, 1])

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Files")
    uploaded_file = st.file_uploader("Upload 360° Panorama", type=['jpg', 'png', 'jpeg'])
    st.divider()
    if st.button("🔥 Reset Application", help="Wipe image and all data", use_container_width=True):
        reset_app()

# --- DATA & INSTRUCTIONS COLUMN ---
with col_data:
    st.subheader("📖 How to use")
    st.markdown("""
    1. **Start:** Click the **Black North Line** at the bottom (359°).
    2. **Trace:** Move **Clockwise** (to the left) along your horizon.
    3. **Lock:** New points must have a lower Azimuth than the previous point.
    4. **Save:** Download the `.txt` file for Stellarium or NINA.
    """)

    st.info("""
    **Legend:**
    * 🟡 **Yellow Circle:** True Horizon (0° Elevation).
    * 🔴 **Red Line:** Angle Limiter (Current Azimuth).
    * 🟢 **Green Path:** Logged Horizon Profile.
    * ⚫ **Black Line:** North Reference (359°).
    * ⚪ **White Cross:** Zenith (90° Elevation).
    """)

    if st.session_state.points:
        lp = st.session_state.points[-1]
        st.success(f"**Current:** Az: {lp['az']}° | El: {lp['el']}°")

    st.subheader("📋 Recorded Data")
    # Sort for the visible log
    final_sorted = sorted(st.session_state.points, key=lambda x: x['az'])
    txt = "\n".join([f"{p['az']} {p['el']}" for p in final_sorted])
    st.text_area("Sorted Log Output", txt, height=350)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⏪ Undo", use_container_width=True):
            if st.session_state.points:
                st.session_state.points.pop(); st.session_state.last_click = None; st.rerun()
    with c2:
        if st.button("🗑️ Clear Points", use_container_width=True):
            st.session_state.points = []; st.session_state.last_click = None; st.rerun()
            
    if st.session_state.points:
        st.download_button("💾 Download .txt", txt, file_name="horizon.txt", use_container_width=True)

# --- INTERACTIVE MAP COLUMN ---
with col_map:
    if uploaded_file:
        img_rgb, center, horizon_r = get_zoomed_polar(uploaded_file.getvalue(), PADDING)
        display_pil = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(display_pil)
        size = center * 2

        # 1. Guides
        draw.ellipse([center-horizon_r, center-horizon_r, center+horizon_r, center+horizon_r], outline="yellow", width=2)
        draw.line([center, center, center, size], fill="black", width=2)
        cs = 15 # Zenith Cross size
        draw.line([center-cs, center, center+cs, center], fill="white", width=2)
        draw.line([center, center-cs, center, center+cs], fill="white", width=2)

        # 2. Clockwise Arrow & Start Label
        arrow_r = horizon_r * 0.35
        draw.arc([center-arrow_r, center-arrow_r, center+arrow_r, center+arrow_r], start=90, end=145, fill="black", width=3)
        # Arrowhead math (tangent rotation)
        tip_a = math.radians(145)
        tx, ty = center + arrow_r * math.cos(tip_a), center + arrow_r * math.sin(tip_a)
        tang_a = tip_a + math.radians(90)
        p1 = (tx + 12 * math.cos(tang_a), ty + 12 * math.sin(tang_a))
        p2 = (tx + 6 * math.cos(tang_a + 2.4), ty + 6 * math.sin(tang_a + 2.4))
        p3 = (tx + 6 * math.cos(tang_a - 2.4), ty + 6 * math.sin(tang_a - 2.4))
        draw.polygon([p1, p2, p3], fill="black")
        draw.text((center + 10, center + arrow_r + 5), "START →", fill="black")

        # 3. Compass Labels
        labels = [(center+15, size-45, "359(N)"), (center+15, 20, "180(S)"), (20, center-20, "270(W)"), (size-85, center-20, "90(E)"), (center+15, center-30, "Zenith")]
        for lx, ly, ltxt in labels:
            for ox, oy in [(-1,-1), (1,1), (-1,1), (1,-1)]:
                draw.text((lx+ox, ly+oy), ltxt, fill="white")
            draw.text((lx, ly), ltxt, fill="black")

        # 4. Path & Vector Interaction
        current_pts = st.session_state.points
        for i, p in enumerate(current_pts):
            draw.ellipse([p['x']-3, p['y']-3, p['x']+3, p['y']+3], fill="green")
            if i > 0:
                draw.line([current_pts[i-1]['x'], current_pts[i-1]['y'], p['x'], p['y']], fill="#00FF00", width=2)
        if current_pts:
            draw.line([center, center, current_pts[-1]['x'], current_pts[-1]['y']], fill="red", width=2)

        # Coordinate detection
        value = streamlit_image_coordinates(display_pil, key="horizon_map", width=800, height=800)
        
        if value and value != st.session_state.last_click:
            vx, vy = value['x'], value['y']
            dx, dy = vx - center, vy - center
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist <= horizon_r:
                az_val = (math.degrees(math.atan2(dx, dy)) + 360) % 360
                az_f = 359 if (az_val < 0.5 or az_val >= 359.5) else int(round(az_val))
                el_f = int(round(90 * (1 - (dist / horizon_r))))
                
                # Check for clockwise sequence
                if not current_pts or az_f < current_pts[-1]['az']:
                    st.session_state.points.append({"x": vx, "y": vy, "az": az_f, "el": el_f})
                    st.session_state.last_click = value 
                    st.rerun()
                else:
                    st.toast("Click Clockwise (Lower Azimuth)!", icon="❌")
    else:
        st.info("Upload your panorama to begin.")