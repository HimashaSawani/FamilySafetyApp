/**
 * AegisSafe Mobile App Controller (Polished UI & Interactions)
 * Real-time Telemetry, Animated SOS Hold Progress, Auto-Fit Leaflet Maps
 */

class MobileSafetyApp {
    constructor() {
        this.apiBase = "http://localhost:8000";
        this.wsUrl = "ws://localhost:8000/ws/telemetry";
        this.circleId = "FAM-9021";

        this.members = {};
        this.geofences = [];
        this.activeSos = [];
        this.currentTab = 'home';
        
        this.miniMap = null;
        this.fullMap = null;
        this.fullMarkers = {};
        this.miniMarkers = {};
        this.fullGeofenceLayers = [];
        this.currentRouteLayer = null;
        this.selectedMapMember = null;
        
        this.sosHoldInterval = null;
        this.sosHoldProgress = 0;
        this.sosDurationMs = 3000;
        this.enteredPin = "";

        this.init();
    }

    async init() {
        this.initClock();
        this.initEventListeners();
        await this.fetchCircleData();
        this.initMaps();
        this.initWebSocket();
        lucide.createIcons();
    }

    initClock() {
        const update = () => {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const mins = String(now.getMinutes()).padStart(2, '0');
            const el = document.getElementById('statusClock');
            if (el) el.innerText = `${hours}:${mins}`;
        };
        update();
        setInterval(update, 10000);
    }

    initEventListeners() {
        // Home SOS Hold Interaction with Animated Progress Bar
        const homeSosBtn = document.getElementById('btnHomeSosTrigger');
        const homeProgressBar = document.getElementById('homeSosProgress');
        const homeInstruction = document.getElementById('homeSosInstruction');

        if (homeSosBtn) {
            this.bindHoldButton(homeSosBtn, homeProgressBar, homeInstruction, () => {
                this.switchTab('sos');
                this.triggerSos();
            });
        }

        // Giant SOS Button (Screen 3) with Animated Progress Bar
        const giantBtn = document.getElementById('btnGiantSos');
        const giantProgressBar = document.getElementById('giantSosProgress');
        const giantInstruction = document.getElementById('sosInstructionText');

        if (giantBtn) {
            this.bindHoldButton(giantBtn, giantProgressBar, giantInstruction, () => {
                this.triggerSos();
            });
        }

        // "I Am Safe" Button
        document.getElementById('btnIamSafe')?.addEventListener('click', () => {
            this.openPinModal();
        });

        // Map Buttons
        document.getElementById('btnCenterGps')?.addEventListener('click', () => {
            if (this.fullMap) {
                this.fitAllMarkersToMap(this.fullMap);
            }
        });
        document.getElementById('btnZoomIn')?.addEventListener('click', () => {
            if (this.fullMap) this.fullMap.zoomIn();
        });
        document.getElementById('btnZoomOut')?.addEventListener('click', () => {
            if (this.fullMap) this.fullMap.zoomOut();
        });

        document.getElementById('btnSheetCall')?.addEventListener('click', () => {
            const target = this.selectedMapMember || this.members['usr_grandpa'] || { phone: '+94705550192', name: 'Grandpa Joe' };
            window.location.href = `tel:${target.phone || '+94705550192'}`;
        });

        document.getElementById('btnSheetDirections')?.addEventListener('click', () => {
            this.handleDirectionsAction();
        });
    }

    bindHoldButton(buttonEl, progressEl, instructionEl, onCompleteCallback) {
        if (!buttonEl) return;

        let startTime = 0;

        const startHold = (e) => {
            e.preventDefault();
            this.sosHoldProgress = 0;
            startTime = Date.now();
            if (instructionEl) {
                instructionEl.innerText = "Holding... (3s)";
                instructionEl.style.color = "#EF4444";
            }

            this.sosHoldInterval = setInterval(() => {
                const elapsed = Date.now() - startTime;
                const percent = Math.min(100, (elapsed / this.sosDurationMs) * 100);
                this.sosHoldProgress = percent;

                if (progressEl) {
                    if (progressEl.id === 'giantSosProgress') progressEl.style.height = `${percent}%`;
                    else progressEl.style.width = `${percent}%`;
                }

                if (elapsed >= this.sosDurationMs) {
                    cancelHold();
                    onCompleteCallback();
                }
            }, 30);
        };

        const cancelHold = () => {
            if (this.sosHoldInterval) {
                clearInterval(this.sosHoldInterval);
                this.sosHoldInterval = null;
            }
            if (progressEl) {
                progressEl.style.width = '0%';
                progressEl.style.height = '0%';
            }
            if (instructionEl) {
                instructionEl.innerText = "Hold for 3 seconds";
                instructionEl.style.color = "#64748B";
            }
        };

        buttonEl.addEventListener('mousedown', startHold);
        buttonEl.addEventListener('mouseup', cancelHold);
        buttonEl.addEventListener('mouseleave', cancelHold);
        buttonEl.addEventListener('touchstart', startHold);
        buttonEl.addEventListener('touchend', cancelHold);
    }

    handleDirectionsAction() {
        const target = this.selectedMapMember || this.members['usr_grandpa'] || { location: { lat: 6.8950, lng: 79.8560 }, name: 'Grandpa Joe' };
        const destLat = target.location?.lat || 6.8950;
        const destLng = target.location?.lng || 79.8560;

        // 1. Draw animated Route Polyline on Map
        this.drawRouteOnMap([6.9360, 79.8450], [destLat, destLng], target.name);

        // 2. Open Real GPS Turn-by-Turn in Google Maps
        const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${destLat},${destLng}&travelmode=driving`;
        window.open(googleMapsUrl, '_blank');
    }

    drawRouteOnMap(startLatLng, endLatLng, targetName) {
        if (!this.fullMap) return;

        if (this.currentRouteLayer) {
            this.fullMap.removeLayer(this.currentRouteLayer);
        }

        const routePoints = [
            startLatLng,
            [6.9271, 79.8480], // Galle Face
            [6.9150, 79.8510], // Kollupitiya
            [6.9050, 79.8540], // Bambalapitiya North
            endLatLng
        ];

        this.currentRouteLayer = L.polyline(routePoints, {
            color: '#2563EB',
            weight: 5,
            opacity: 0.85,
            dashArray: '8, 8',
            lineCap: 'round'
        }).addTo(this.fullMap);

        this.fullMap.fitBounds(this.currentRouteLayer.getBounds(), { padding: [40, 40] });
    }

    switchTab(tabName) {
        this.currentTab = tabName;

        const screens = ['screenHome', 'screenMap', 'screenSos', 'screenAlerts', 'screenSettings'];
        screens.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.remove('active');
        });

        const targetMap = {
            'home': 'screenHome',
            'map': 'screenMap',
            'sos': 'screenSos',
            'alerts': 'screenAlerts',
            'settings': 'screenSettings'
        };
        const targetEl = document.getElementById(targetMap[tabName] || 'screenHome');
        if (targetEl) targetEl.classList.add('active');

        document.querySelectorAll('.nav-item').forEach(btn => {
            if (btn.getAttribute('data-tab') === tabName) btn.classList.add('active');
            else btn.classList.remove('active');
        });

        // Ensure Leaflet map recalculates viewport with all members properly visible
        if (tabName === 'map' && this.fullMap) {
            setTimeout(() => {
                this.fullMap.invalidateSize();
                this.fitAllMarkersToMap(this.fullMap);
            }, 200);
        }
        if (tabName === 'home' && this.miniMap) {
            setTimeout(() => {
                this.miniMap.invalidateSize();
                this.fitAllMarkersToMap(this.miniMap);
            }, 200);
        }

        lucide.createIcons();
    }

    async fetchCircleData() {
        try {
            const res = await fetch(`${this.apiBase}/api/circle/${this.circleId}`);
            if (!res.ok) throw new Error("Failed to fetch circle data");
            const data = await res.json();
            
            this.members = {};
            data.members.forEach(m => this.members[m.id] = m);
            this.geofences = data.geofences || [];
            this.activeSos = data.active_sos || [];

            this.renderHomeMembers();
            this.renderSosContacts();
            this.renderAlerts(data.logs || []);
            this.updateOnlineCount();
            this.updateAlertBadge();
        } catch (e) {
            console.error("API error:", e);
        }
    }

    initMaps() {
        const colomboCenter = [6.9271, 79.8612];

        // 1. Mini Map on Home Tab
        const miniEl = document.getElementById('miniMap');
        if (miniEl) {
            this.miniMap = L.map('miniMap', {
                center: colomboCenter,
                zoom: 12,
                zoomControl: false,
                attributionControl: false,
                dragging: false,
                touchZoom: false,
                scrollWheelZoom: false,
                doubleClickZoom: false
            });

            // Standard OpenStreetMap (100% Free - NO API KEY REQUIRED)
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(this.miniMap);
        }

        // 2. Fullscreen Map on Map Tab
        const fullEl = document.getElementById('fullMap');
        if (fullEl) {
            this.fullMap = L.map('fullMap', {
                center: colomboCenter,
                zoom: 13,
                zoomControl: false,
                attributionControl: false
            });

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(this.fullMap);
        }

        this.renderMapMarkers();
    }

    renderMapMarkers() {
        if (!this.miniMap || !this.fullMap) return;

        // Render Members
        Object.values(this.members).forEach(m => {
            if (!m.location) return;
            const latLng = [m.location.lat, m.location.lng];
            const iconHtml = `
                <div class="custom-map-avatar-marker">
                    <div class="marker-avatar-circle" style="background-image: url('${m.avatar_url}'); border-color: ${m.color};"></div>
                    <div class="marker-pin-tip" style="background:${m.color};"></div>
                </div>
            `;
            const customIcon = L.divIcon({
                className: 'custom-leaflet-pin',
                html: iconHtml,
                iconSize: [42, 48],
                iconAnchor: [21, 48]
            });

            // Mini Map Marker
            if (this.miniMarkers[m.id]) {
                this.miniMarkers[m.id].setLatLng(latLng);
            } else {
                this.miniMarkers[m.id] = L.marker(latLng, { icon: customIcon }).addTo(this.miniMap);
            }

            // Full Map Marker
            if (this.fullMarkers[m.id]) {
                this.fullMarkers[m.id].setLatLng(latLng);
            } else {
                const marker = L.marker(latLng, { icon: customIcon }).addTo(this.fullMap);
                marker.on('click', () => {
                    this.selectMemberOnMap(m);
                });
                this.fullMarkers[m.id] = marker;
            }
        });

        // Geofences
        this.fullGeofenceLayers.forEach(l => this.fullMap.removeLayer(l));
        this.fullGeofenceLayers = [];

        this.geofences.forEach(g => {
            const circle = L.circle([g.lat, g.lng], {
                radius: g.radius,
                color: '#3B82F6',
                fillColor: '#3B82F6',
                fillOpacity: 0.12,
                weight: 2
            }).addTo(this.fullMap);
            this.fullGeofenceLayers.push(circle);
        });

        this.fitAllMarkersToMap(this.miniMap);
        this.fitAllMarkersToMap(this.fullMap);
    }

    fitAllMarkersToMap(mapInstance) {
        if (!mapInstance) return;
        const latLngs = Object.values(this.members)
            .filter(m => m.location)
            .map(m => [m.location.lat, m.location.lng]);

        if (latLngs.length > 0) {
            const bounds = L.latLngBounds(latLngs);
            mapInstance.fitBounds(bounds, { padding: [35, 35], maxZoom: 14 });
        }
    }

    selectMemberOnMap(m) {
        this.selectedMapMember = m;
        document.getElementById('sheetMemberName').innerText = m.name;
        document.getElementById('sheetAvatar').src = m.avatar_url;
        
        const isMove = m.status_text?.toLowerCase().includes('move');
        document.getElementById('sheetMemberStatus').innerText = isMove ? 'On the move' : 'At home';
        document.getElementById('sheetFreshnessText').innerText = m.freshness || 'Updated just now';
        document.getElementById('sheetBatteryPercent').innerText = `${m.battery}%`;

        this.fullMap.flyTo([m.location.lat, m.location.lng], 15, { animate: true });
    }

    renderHomeMembers() {
        const list = document.getElementById('homeMembersList');
        if (!list) return;
        list.innerHTML = '';

        Object.values(this.members).forEach(m => {
            const isMove = m.status_text?.toLowerCase().includes('move');
            const dotClass = isMove ? 'blue' : 'green';
            const statusLabel = isMove ? 'On the move' : 'At home';
            const freshnessLabel = m.freshness ? `Updated ${m.freshness.toLowerCase()}` : 'Updated just now';
            const batteryClass = m.battery > 50 ? 'good' : 'med';

            const card = document.createElement('div');
            card.className = 'member-card';
            card.innerHTML = `
                <img src="${m.avatar_url}" class="member-avatar-img" alt="${m.name}">
                <div class="member-info-col">
                    <div class="member-top-name">${m.name}</div>
                    <div class="member-status-line">
                        <span class="status-dot-small ${dotClass}"></span>
                        <span>${statusLabel}</span>
                    </div>
                    <div class="member-freshness-line">
                        <i data-lucide="clock" class="w-3 h-3 text-muted"></i>
                        <span>${freshnessLabel}</span>
                    </div>
                </div>
                <div class="member-battery-col">
                    <div class="battery-pill ${batteryClass}">
                        <i data-lucide="battery-medium" class="w-3.5 h-3.5"></i>
                        <span>${m.battery}%</span>
                    </div>
                    <i data-lucide="chevron-right" class="w-4 h-4 text-muted"></i>
                </div>
            `;
            card.onclick = () => {
                this.selectMemberOnMap(m);
                this.switchTab('map');
            };
            list.appendChild(card);
        });
        lucide.createIcons();
    }

    renderSosContacts() {
        const list = document.getElementById('sosContactsList');
        if (!list) return;
        list.innerHTML = '';

        const contacts = [
            this.members['usr_sarah'] || { name: 'Sarah', role: 'Guardian', avatar_url: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150', phone: '+94 77 123 4567' },
            this.members['usr_leo'] || { name: 'Leo', role: 'Family', avatar_url: 'https://images.unsplash.com/photo-1543610892-0b1f7e6d8ac1?w=150', phone: '+94 71 987 6543' }
        ];

        contacts.forEach(c => {
            const item = document.createElement('div');
            item.className = 'sos-contact-item';
            item.innerHTML = `
                <img src="${c.avatar_url}" class="sos-contact-avatar" alt="${c.name}">
                <div class="sos-contact-info">
                    <div class="sos-contact-name">${c.name}</div>
                    <div class="sos-contact-role">${c.role}</div>
                </div>
                <button class="btn-contact-call" onclick="window.location.href='tel:${c.phone}'" title="Call">
                    <i data-lucide="phone"></i>
                </button>
            `;
            list.appendChild(item);
        });
        lucide.createIcons();
    }

    renderAlerts(logs) {
        const container = document.getElementById('alertsLogContainer');
        if (!container) return;
        container.innerHTML = '';

        logs.forEach(l => {
            const card = document.createElement('div');
            card.className = `alert-item-card ${l.level}`;
            const timeStr = new Date(l.timestamp).toLocaleTimeString();
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.75rem;">
                    <strong style="color:${l.level === 'CRITICAL' ? '#EF4444' : '#2563EB'}">${l.category}</strong>
                    <span style="color:#64748B;">${timeStr}</span>
                </div>
                <p style="font-size:0.8rem; color:#0F172A;">${l.message}</p>
            `;
            container.appendChild(card);
        });
    }

    updateOnlineCount() {
        const count = Object.keys(this.members).length;
        const el = document.getElementById('homeOnlineCount');
        if (el) el.innerText = `${count} members online`;
    }

    updateAlertBadge() {
        const badge = document.getElementById('alertBadge');
        if (!badge) return;
        if (this.activeSos.length > 0) {
            badge.innerText = String(this.activeSos.length);
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    clearAlertsBadge() {
        const badge = document.getElementById('alertBadge');
        if (badge) badge.classList.add('hidden');
    }

    async triggerSos() {
        const instruction = document.getElementById('sosInstructionText');
        const deliveryCard = document.getElementById('sosDeliveryCard');

        try {
            const res = await fetch(`${this.apiBase}/api/sos/trigger`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: 'usr_sarah',
                    location_name: 'Colombo Fort, Sri Lanka'
                })
            });
            if (res.ok) {
                const data = await res.json();
                if (instruction) {
                    instruction.innerText = "🚨 DISTRESS BEACON ACTIVE!";
                    instruction.style.color = "#EF4444";
                }
                if (deliveryCard) {
                    deliveryCard.classList.remove('hidden');
                    document.getElementById('sosDeliverySubtitle').innerText = data.alert?.delivery_status || 'Delivered to 3 family members via Cloud & SMS';
                }
                this.updateAlertBadge();
            }
        } catch (e) {
            alert("Error sending SOS broadcast to backend.");
        }
    }

    openPinModal() {
        this.enteredPin = "";
        this.updatePinDots();
        document.getElementById('pinModal').classList.remove('hidden');
    }

    closePinModal() {
        document.getElementById('pinModal').classList.add('hidden');
    }

    appendPin(num) {
        if (this.enteredPin.length < 4) {
            this.enteredPin += num;
            this.updatePinDots();
            if (this.enteredPin.length === 4) {
                setTimeout(() => this.submitPin(), 200);
            }
        }
    }

    clearPin() {
        this.enteredPin = "";
        this.updatePinDots();
    }

    updatePinDots() {
        for (let i = 1; i <= 4; i++) {
            const dot = document.getElementById(`pDot${i}`);
            if (dot) {
                if (i <= this.enteredPin.length) dot.classList.add('filled');
                else dot.classList.remove('filled');
            }
        }
    }

    async submitPin() {
        if (this.enteredPin.length !== 4) return;

        try {
            const res = await fetch(`${this.apiBase}/api/sos/cancel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sos_id: this.activeSos.length > 0 ? this.activeSos[0].id : 'SOS-1791244498',
                    user_id: 'usr_sarah',
                    pin: this.enteredPin,
                    resolution_notes: 'Verified safe by guardian on mobile app.'
                })
            });

            if (res.ok) {
                this.closePinModal();
                alert("🟢 Safety confirmed! SOS Alert Cancelled & Resolved.");
                const instruction = document.getElementById('sosInstructionText');
                const deliveryCard = document.getElementById('sosDeliveryCard');
                if (instruction) {
                    instruction.innerText = "Hold for 3 seconds";
                    instruction.style.color = "#64748B";
                }
                if (deliveryCard) deliveryCard.classList.add('hidden');
                this.fetchCircleData();
            } else if (res.status === 403) {
                alert("❌ Invalid PIN. Server rejected cancellation request.");
                this.clearPin();
            }
        } catch (e) {
            this.closePinModal();
        }
    }

    toggleLocationPrivacy(isEnabled) {
        const label = document.getElementById('privacyStatusLabel');
        if (label) {
            label.innerText = isEnabled ? "Visible to Walker Family Circle" : "Location sharing PAUSED (Private)";
            label.style.color = isEnabled ? "#64748B" : "#EF4444";
        }
    }

    initWebSocket() {
        const connect = () => {
            const ws = new WebSocket(this.wsUrl);
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'LOCATION_UPDATED') {
                        if (this.members[data.user_id]) {
                            this.members[data.user_id].location = data.location;
                            this.members[data.user_id].battery = data.battery;
                            this.renderHomeMembers();
                            this.renderMapMarkers();
                        }
                    } else if (data.type === 'SOS_TRIGGERED') {
                        this.fetchCircleData();
                    }
                } catch (e) {}
            };
            ws.onclose = () => setTimeout(connect, 4000);
        };
        connect();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new MobileSafetyApp();
    });
} else {
    window.app = new MobileSafetyApp();
}
