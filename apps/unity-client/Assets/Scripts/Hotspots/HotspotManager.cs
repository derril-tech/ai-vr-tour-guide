using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;

namespace VRTourGuide.Hotspots
{
    /// <summary>
    /// Manages interactive hotspots throughout the VR tour
    /// Handles hotspot creation, interaction, and visual feedback
    /// </summary>
    public class HotspotManager : MonoBehaviour
    {
        [Header("Hotspot Prefabs")]
        [SerializeField] private GameObject informationHotspotPrefab;
        [SerializeField] private GameObject navigationHotspotPrefab;
        [SerializeField] private GameObject interactiveHotspotPrefab;
        [SerializeField] private GameObject quizHotspotPrefab;
        
        [Header("Visual Settings")]
        [SerializeField] private Material hotspotMaterial;
        [SerializeField] private Material highlightMaterial;
        [SerializeField] private float pulseSpeed = 2f;
        [SerializeField] private float glowIntensity = 1.5f;
        
        [Header("Audio")]
        [SerializeField] private AudioClip hoverSound;
        [SerializeField] private AudioClip activateSound;
        [SerializeField] private AudioSource audioSource;
        
        // Hotspot management
        private Dictionary<string, HotspotController> activeHotspots = new Dictionary<string, HotspotController>();
        private Transform hotspotsParent;
        
        // Interaction
        private HotspotController hoveredHotspot;
        private Camera playerCamera;
        
        // Events
        public System.Action<Hotspot> OnHotspotActivated;
        public System.Action<Hotspot> OnHotspotHovered;
        
        private void Start()
        {
            Initialize();
        }
        
        private void Initialize()
        {
            // Create hotspots parent
            hotspotsParent = new GameObject("Hotspots").transform;
            hotspotsParent.SetParent(transform);
            
            // Get player camera
            playerCamera = Camera.main;
            if (playerCamera == null)
            {
                playerCamera = FindObjectOfType<Camera>();
            }
            
            Debug.Log("Hotspot Manager initialized");
        }
        
        public void LoadHotspots(List<Hotspot> hotspots)
        {
            // Clear existing hotspots
            ClearHotspots();
            
            // Create new hotspots
            foreach (var hotspot in hotspots)
            {
                CreateHotspot(hotspot);
            }
            
            Debug.Log($"Loaded {hotspots.Count} hotspots");
        }
        
        private void CreateHotspot(Hotspot hotspotData)
        {
            GameObject prefab = GetHotspotPrefab(hotspotData.type);
            if (prefab == null)
            {
                Debug.LogError($"No prefab found for hotspot type: {hotspotData.type}");
                return;
            }
            
            // Instantiate hotspot
            GameObject hotspotObj = Instantiate(prefab, hotspotsParent);
            hotspotObj.name = $"Hotspot_{hotspotData.id}";
            hotspotObj.transform.position = hotspotData.position;
            hotspotObj.transform.rotation = hotspotData.rotation;
            hotspotObj.transform.localScale = hotspotData.scale;
            
            // Setup hotspot controller
            var controller = hotspotObj.GetComponent<HotspotController>();
            if (controller == null)
            {
                controller = hotspotObj.AddComponent<HotspotController>();
            }
            
            controller.Initialize(hotspotData, this);
            
            // Setup XR interaction
            SetupXRInteraction(hotspotObj, controller);
            
            // Add to active hotspots
            activeHotspots[hotspotData.id] = controller;
        }
        
        private GameObject GetHotspotPrefab(HotspotType type)
        {
            switch (type)
            {
                case HotspotType.Information:
                    return informationHotspotPrefab;
                case HotspotType.Navigation:
                    return navigationHotspotPrefab;
                case HotspotType.Interactive:
                    return interactiveHotspotPrefab;
                case HotspotType.Quiz:
                    return quizHotspotPrefab;
                default:
                    return informationHotspotPrefab;
            }
        }
        
        private void SetupXRInteraction(GameObject hotspotObj, HotspotController controller)
        {
            // Add XR interactable component
            var interactable = hotspotObj.GetComponent<XRGrabInteractable>();
            if (interactable == null)
            {
                interactable = hotspotObj.AddComponent<XRSimpleInteractable>();
            }
            
            // Setup interaction events
            interactable.hoverEntered.AddListener((args) => OnHotspotHover(controller, true));
            interactable.hoverExited.AddListener((args) => OnHotspotHover(controller, false));
            interactable.selectEntered.AddListener((args) => OnHotspotSelect(controller));
            
            // Ensure collider exists
            var collider = hotspotObj.GetComponent<Collider>();
            if (collider == null)
            {
                var sphereCollider = hotspotObj.AddComponent<SphereCollider>();
                sphereCollider.radius = 0.5f;
                sphereCollider.isTrigger = true;
            }
        }
        
        private void OnHotspotHover(HotspotController controller, bool isHovering)
        {
            if (isHovering)
            {
                hoveredHotspot = controller;
                controller.SetHighlighted(true);
                PlayHoverSound();
                OnHotspotHovered?.Invoke(controller.HotspotData);
            }
            else
            {
                if (hoveredHotspot == controller)
                {
                    hoveredHotspot = null;
                }
                controller.SetHighlighted(false);
            }
        }
        
        private void OnHotspotSelect(HotspotController controller)
        {
            PlayActivateSound();
            controller.Activate();
            OnHotspotActivated?.Invoke(controller.HotspotData);
        }
        
        private void PlayHoverSound()
        {
            if (hoverSound != null && audioSource != null)
            {
                audioSource.PlayOneShot(hoverSound);
            }
        }
        
        private void PlayActivateSound()
        {
            if (activateSound != null && audioSource != null)
            {
                audioSource.PlayOneShot(activateSound);
            }
        }
        
        public void ClearHotspots()
        {
            foreach (var controller in activeHotspots.Values)
            {
                if (controller != null && controller.gameObject != null)
                {
                    Destroy(controller.gameObject);
                }
            }
            
            activeHotspots.Clear();
            hoveredHotspot = null;
        }
        
        public void SetHotspotVisibility(string hotspotId, bool visible)
        {
            if (activeHotspots.TryGetValue(hotspotId, out HotspotController controller))
            {
                controller.SetVisible(visible);
            }
        }
        
        public void SetAllHotspotsVisibility(bool visible)
        {
            foreach (var controller in activeHotspots.Values)
            {
                controller.SetVisible(visible);
            }
        }
        
        public HotspotController GetHotspot(string hotspotId)
        {
            activeHotspots.TryGetValue(hotspotId, out HotspotController controller);
            return controller;
        }
        
        public List<HotspotController> GetAllHotspots()
        {
            return new List<HotspotController>(activeHotspots.Values);
        }
        
        public void UpdateHotspotVisibility()
        {
            if (playerCamera == null) return;
            
            Vector3 cameraPos = playerCamera.transform.position;
            Vector3 cameraForward = playerCamera.transform.forward;
            
            foreach (var controller in activeHotspots.Values)
            {
                if (controller == null) continue;
                
                // Distance-based visibility
                float distance = Vector3.Distance(cameraPos, controller.transform.position);
                bool inRange = distance <= controller.HotspotData.visibilityRange;
                
                // Angle-based visibility (optional)
                bool inView = true;
                if (controller.HotspotData.requiresLineOfSight)
                {
                    Vector3 directionToHotspot = (controller.transform.position - cameraPos).normalized;
                    float angle = Vector3.Angle(cameraForward, directionToHotspot);
                    inView = angle <= controller.HotspotData.visibilityAngle;
                }
                
                controller.SetVisible(inRange && inView);
            }
        }
        
        private void Update()
        {
            UpdateHotspotVisibility();
            UpdateHotspotAnimations();
        }
        
        private void UpdateHotspotAnimations()
        {
            foreach (var controller in activeHotspots.Values)
            {
                if (controller != null && controller.gameObject.activeInHierarchy)
                {
                    controller.UpdateAnimation(Time.time);
                }
            }
        }
    }
    
    /// <summary>
    /// Individual hotspot controller
    /// </summary>
    public class HotspotController : MonoBehaviour
    {
        private Hotspot hotspotData;
        private HotspotManager manager;
        private Renderer hotspotRenderer;
        private Material originalMaterial;
        private bool isHighlighted = false;
        private bool isVisible = true;
        
        // Animation
        private float pulsePhase = 0f;
        private Vector3 originalScale;
        
        public Hotspot HotspotData => hotspotData;
        
        public void Initialize(Hotspot data, HotspotManager mgr)
        {
            hotspotData = data;
            manager = mgr;
            
            hotspotRenderer = GetComponent<Renderer>();
            if (hotspotRenderer != null)
            {
                originalMaterial = hotspotRenderer.material;
            }
            
            originalScale = transform.localScale;
            pulsePhase = Random.Range(0f, Mathf.PI * 2f); // Random phase for variety
            
            // Setup visual appearance based on type
            SetupVisualAppearance();
        }
        
        private void SetupVisualAppearance()
        {
            if (hotspotRenderer == null) return;
            
            // Set color based on hotspot type
            Color hotspotColor = GetTypeColor(hotspotData.type);
            
            if (originalMaterial != null)
            {
                var material = new Material(originalMaterial);
                material.color = hotspotColor;
                hotspotRenderer.material = material;
            }
        }
        
        private Color GetTypeColor(HotspotType type)
        {
            switch (type)
            {
                case HotspotType.Information:
                    return Color.blue;
                case HotspotType.Navigation:
                    return Color.green;
                case HotspotType.Interactive:
                    return Color.yellow;
                case HotspotType.Quiz:
                    return Color.magenta;
                default:
                    return Color.white;
            }
        }
        
        public void SetHighlighted(bool highlighted)
        {
            isHighlighted = highlighted;
            
            if (hotspotRenderer != null && manager != null)
            {
                if (highlighted && manager.highlightMaterial != null)
                {
                    hotspotRenderer.material = manager.highlightMaterial;
                }
                else if (originalMaterial != null)
                {
                    hotspotRenderer.material = originalMaterial;
                }
            }
        }
        
        public void SetVisible(bool visible)
        {
            isVisible = visible;
            gameObject.SetActive(visible);
        }
        
        public void Activate()
        {
            // Trigger activation animation
            StartCoroutine(ActivationAnimation());
        }
        
        private IEnumerator ActivationAnimation()
        {
            Vector3 targetScale = originalScale * 1.2f;
            float duration = 0.2f;
            float elapsed = 0f;
            
            while (elapsed < duration)
            {
                float t = elapsed / duration;
                transform.localScale = Vector3.Lerp(originalScale, targetScale, t);
                elapsed += Time.deltaTime;
                yield return null;
            }
            
            // Scale back
            elapsed = 0f;
            while (elapsed < duration)
            {
                float t = elapsed / duration;
                transform.localScale = Vector3.Lerp(targetScale, originalScale, t);
                elapsed += Time.deltaTime;
                yield return null;
            }
            
            transform.localScale = originalScale;
        }
        
        public void UpdateAnimation(float time)
        {
            if (!isVisible) return;
            
            // Pulse animation
            if (manager != null)
            {
                float pulse = Mathf.Sin(time * manager.pulseSpeed + pulsePhase) * 0.1f + 1f;
                transform.localScale = originalScale * pulse;
                
                // Glow effect for highlighted hotspots
                if (isHighlighted && hotspotRenderer != null)
                {
                    float glow = Mathf.Sin(time * manager.pulseSpeed * 2f) * 0.5f + 1f;
                    var material = hotspotRenderer.material;
                    if (material.HasProperty("_EmissionColor"))
                    {
                        material.SetColor("_EmissionColor", GetTypeColor(hotspotData.type) * glow * manager.glowIntensity);
                    }
                }
            }
        }
    }
}
