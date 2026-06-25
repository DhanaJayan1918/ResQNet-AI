/**
 * ResQNet AI - Incident Report Form Component
 * Premium dark-themed form with glassmorphism, Framer Motion animations,
 * and an interactive Leaflet map to pin incident coordinates.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapContainer, TileLayer, Marker, useMapEvents
} from 'react-leaflet';
import L from 'leaflet';
import {
  MapPin, Upload, AlertTriangle, CheckCircle2, Loader2, X, AlertOctagon, HelpCircle
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { incidentsApi } from '../../api/incidents';
import { cn } from '../../lib/utils';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default marker icon bug in React
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Default map center (Chennai, India context matching seed data)
const CHENNAI_CENTER: [number, number] = [13.0827, 80.2707];

interface MapSelectorProps {
  position: [number, number] | null;
  setPosition: (pos: [number, number]) => void;
}

// Map helper to register click event and place marker
function MapSelector({ position, setPosition }: MapSelectorProps) {
  const map = useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      setPosition([lat, lng]);
      map.flyTo(e.latlng, map.getZoom());
    },
  });

  // Automatically locate user's device GPS coordinates if requested
  useEffect(() => {
    if (!position) {
      map.locate();
    }
  }, []);

  useMapEvents({
    locationfound(e) {
      const { lat, lng } = e.latlng;
      setPosition([lat, lng]);
      map.flyTo(e.latlng, 14);
    },
  });

  return position === null ? null : (
    <Marker position={position} />
  );
}

export default function ReportForm() {
  const { user } = useAuthStore();
  const [text, setText] = useState('');
  const [coords, setCoords] = useState<[number, number]>(CHENNAI_CENTER);
  const [address, setAddress] = useState('');
  const [landmark, setLandmark] = useState('');
  const [reporterName, setReporterName] = useState(user?.full_name || '');
  const [reporterContact, setReporterContact] = useState(user?.phone || '');
  const [images, setImages] = useState<string[]>([]);
  
  // UI States
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Prefill reporter info when user logs in
  useEffect(() => {
    if (user) {
      setReporterName(user.full_name);
      if (user.phone) setReporterContact(user.phone);
    }
  }, [user]);

  // Handle image upload to API
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('Image size cannot exceed 10MB.');
      return;
    }

    setIsUploading(true);
    setErrorMsg(null);
    try {
      const data = await incidentsApi.uploadImage(file);
      setImages((prev) => [...prev, data.image_url]);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload image. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Remove uploaded image from list
  const handleRemoveImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  // Form submission handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (text.length < 10) {
      setErrorMsg('Please describe the emergency in at least 10 characters.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const payload = {
        text,
        latitude: coords[0],
        longitude: coords[1],
        address: address || undefined,
        landmark: landmark || undefined,
        images,
        source_type: user?.role === 'field_officer' ? 'field_officer' : 'citizen',
        submission_channel: 'web',
        reporter_name: reporterName || undefined,
        reporter_contact: reporterContact || undefined,
        metadata: {}
      };
      
      const res = await incidentsApi.submitIncident(payload);
      setSubmitSuccess(res.incident_id);
      
      // Reset form fields
      setText('');
      setAddress('');
      setLandmark('');
      setImages([]);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass max-w-4xl mx-auto p-6 md:p-8 rounded-xl relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-red-500/10 rounded-full blur-3xl -z-10" />

      <div className="mb-6 flex items-center space-x-3">
        <div className="p-2.5 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20">
          <AlertOctagon className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100">Submit Emergency Report</h2>
          <p className="text-xs text-slate-400">Your report will be processed by AI and routed directly to first responders.</p>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {submitSuccess ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center justify-center py-12 text-center"
          >
            <div className="p-4 bg-emerald-500/10 text-emerald-500 rounded-full border border-emerald-500/20 mb-4">
              <CheckCircle2 className="w-16 h-16 animate-bounce" />
            </div>
            <h3 className="text-2xl font-bold text-slate-100">Report Ingested Successfully</h3>
            <p className="text-sm text-slate-400 mt-2 max-w-md">
              Incident ID: <span className="font-mono text-blue-400 font-semibold">{submitSuccess}</span> has been logged. First responders are being dispatched.
            </p>
            <button
              onClick={() => setSubmitSuccess(null)}
              className="mt-8 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition"
            >
              Submit Another Report
            </button>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Incident Text Description */}
            <div>
              <label htmlFor="text" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Emergency Situation Description <span className="text-red-500">*</span>
              </label>
              <textarea
                id="text"
                rows={4}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Please describe what is happening in detail. Mention the number of people trapped/injured, exact flooding level, structures collapsed, or fire intensity..."
                className="w-full bg-slate-900/60 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg p-3 text-slate-100 placeholder-slate-500 transition resize-none text-sm"
                required
              />
            </div>

            {/* Grid for Map + Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column: Map Selector */}
              <div className="flex flex-col">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex justify-between items-center">
                  <span>Pin Location on Map <span className="text-red-500">*</span></span>
                  <span className="text-[10px] text-slate-500 font-normal">Click map to move pin</span>
                </label>
                <div className="h-[250px] w-full rounded-lg overflow-hidden border border-slate-700 shadow-inner relative">
                  <MapContainer
                    center={coords}
                    zoom={12}
                    scrollWheelZoom={true}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <MapSelector position={coords} setPosition={setCoords} />
                  </MapContainer>
                  
                  {/* Coords overlay */}
                  <div className="absolute bottom-2 left-2 bg-slate-950/80 px-2 py-1 rounded text-[10px] font-mono text-slate-300 z-[1000] border border-slate-700">
                    Lng: {coords[1].toFixed(5)}, Lat: {coords[0].toFixed(5)}
                  </div>
                </div>
              </div>

              {/* Right Column: Location Details + Contact */}
              <div className="space-y-4">
                <div>
                  <label htmlFor="address" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Address / Neighborhood
                  </label>
                  <input
                    id="address"
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="e.g. Velachery Main Road, Chennai"
                    className="w-full bg-slate-900/60 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-500 transition text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="landmark" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Nearby Landmark
                  </label>
                  <input
                    id="landmark"
                    type="text"
                    value={landmark}
                    onChange={(e) => setLandmark(e.target.value)}
                    placeholder="e.g. Opposite Phoenix Marketcity Mall"
                    className="w-full bg-slate-900/60 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-500 transition text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="reporterName" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                      Reporter Name
                    </label>
                    <input
                      id="reporterName"
                      type="text"
                      value={reporterName}
                      onChange={(e) => setReporterName(e.target.value)}
                      placeholder="Anonymous"
                      className="w-full bg-slate-900/60 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-500 transition text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="reporterContact" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                      Reporter Phone
                    </label>
                    <input
                      id="reporterContact"
                      type="text"
                      value={reporterContact}
                      onChange={(e) => setReporterContact(e.target.value)}
                      placeholder="Optional contact details"
                      className="w-full bg-slate-900/60 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-500 transition text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Image Upload section */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Attach Disaster Photos (Max 10MB)
              </label>
              <div className="flex flex-wrap gap-4 items-center">
                {/* Upload box */}
                <label className="w-24 h-24 border border-dashed border-slate-600 hover:border-blue-500 hover:bg-blue-500/5 rounded-lg flex flex-col items-center justify-center cursor-pointer transition relative group">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                    disabled={isUploading}
                  />
                  {isUploading ? (
                    <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                  ) : (
                    <>
                      <Upload className="w-6 h-6 text-slate-500 group-hover:text-blue-400 transition" />
                      <span className="text-[10px] text-slate-500 mt-1">Upload</span>
                    </>
                  )}
                </label>

                {/* Uploaded thumbnails */}
                {images.map((url, idx) => (
                  <div key={idx} className="w-24 h-24 rounded-lg overflow-hidden border border-slate-700 relative group">
                    <img src={url} alt={`Upload ${idx}`} className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(idx)}
                      className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition duration-150"
                    >
                      <X className="w-6 h-6 text-red-500 hover:scale-110 transition" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Error Message */}
            <AnimatePresence>
              {errorMsg && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="p-3.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-sm flex items-start space-x-2.5"
                >
                  <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit Action */}
            <div className="flex justify-end pt-4 border-t border-slate-800">
              <button
                type="submit"
                disabled={isSubmitting || isUploading}
                className={cn(
                  "px-8 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition shadow-lg flex items-center justify-center space-x-2",
                  (isSubmitting || isUploading) && "opacity-50 cursor-not-allowed"
                )}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Ingesting...</span>
                  </>
                ) : (
                  <>
                    <AlertOctagon className="w-5 h-5" />
                    <span>BROADCAST EMERGENCY</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </AnimatePresence>
    </div>
  );
}
