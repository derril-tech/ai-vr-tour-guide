import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

interface Site {
  id: string
  name: string
  description: string
  position: [number, number, number]
  hotspots: Hotspot[]
}

interface Hotspot {
  id: string
  position: [number, number, number]
  title: string
  description: string
  type: 'info' | 'audio' | 'video' | 'quiz'
  content?: any
}

interface AppState {
  // XR Support
  isVRSupported: boolean
  isARSupported: boolean
  isXRActive: boolean
  
  // Current Site & Tour
  currentSite: Site | null
  currentHotspot: Hotspot | null
  
  // UI State
  isLoading: boolean
  showUI: boolean
  
  // Audio/Narration
  isNarrating: boolean
  currentAudio: HTMLAudioElement | null
  
  // Actions
  setXRSupport: (vr: boolean, ar: boolean) => void
  setXRActive: (active: boolean) => void
  setCurrentSite: (site: Site | null) => void
  setCurrentHotspot: (hotspot: Hotspot | null) => void
  setLoading: (loading: boolean) => void
  setShowUI: (show: boolean) => void
  playAudio: (url: string) => void
  stopAudio: () => void
}

export const useStore = create<AppState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    isVRSupported: false,
    isARSupported: false,
    isXRActive: false,
    currentSite: null,
    currentHotspot: null,
    isLoading: false,
    showUI: true,
    isNarrating: false,
    currentAudio: null,

    // Actions
    setXRSupport: (vr, ar) => set({ isVRSupported: vr, isARSupported: ar }),
    
    setXRActive: (active) => set({ isXRActive: active }),
    
    setCurrentSite: (site) => set({ currentSite: site }),
    
    setCurrentHotspot: (hotspot) => set({ currentHotspot: hotspot }),
    
    setLoading: (loading) => set({ isLoading: loading }),
    
    setShowUI: (show) => set({ showUI: show }),
    
    playAudio: (url) => {
      const { currentAudio } = get()
      
      // Stop current audio if playing
      if (currentAudio) {
        currentAudio.pause()
        currentAudio.currentTime = 0
      }
      
      // Create and play new audio
      const audio = new Audio(url)
      audio.play()
      
      audio.onended = () => {
        set({ isNarrating: false, currentAudio: null })
      }
      
      set({ isNarrating: true, currentAudio: audio })
    },
    
    stopAudio: () => {
      const { currentAudio } = get()
      if (currentAudio) {
        currentAudio.pause()
        currentAudio.currentTime = 0
      }
      set({ isNarrating: false, currentAudio: null })
    },
  }))
)
