using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;

namespace VRTourGuide.Comfort
{
    /// <summary>
    /// Manages VR comfort features to prevent motion sickness
    /// Includes vignetting, snap turning, teleportation, and comfort monitoring
    /// </summary>
    public class ComfortManager : MonoBehaviour
    {
        [Header("Comfort Settings")]
        [SerializeField] private bool enableComfortFeatures = true;
        [SerializeField] private ComfortLevel comfortLevel = ComfortLevel.Medium;
        
        [Header("Vignetting")]
        [SerializeField] private bool enableVignetting = true;
        [SerializeField] private Material vignetteMaterial;
        [SerializeField] private float vignetteIntensity = 0.7f;
        [SerializeField] private float vignetteSpeed = 2f;
        
        [Header("Motion Monitoring")]
        [SerializeField] private bool enableMotionMonitoring = true;
        [SerializeField] private float motionSicknessThreshold = 0.8f;
        [SerializeField] private float recoveryTime = 5f;
        
        [Header("Snap Turning")]
        [SerializeField] private bool enableSnapTurning = true;
        [SerializeField] private float snapTurnAngle = 30f;
        [SerializeField] private float snapTurnCooldown = 0.3f;
        
        [Header("Teleportation")]
        [SerializeField] private bool forceTeleportation = false;
        [SerializeField] private GameObject teleportReticle;
        [SerializeField] private LineRenderer teleportLine;
        
        [Header("UI Elements")]
        [SerializeField] private Canvas comfortUI;
        [SerializeField] private UnityEngine.UI.Slider comfortSlider;
        [SerializeField] private TMPro.TextMeshProUGUI comfortText;
        
        // Comfort state
        private float currentComfortScore = 1f;
        private bool isExperiencingDiscomfort = false;
        private float discomfortStartTime;
        private Vector3 lastHeadPosition;
        private Quaternion lastHeadRotation;
        private float accumulatedMotion = 0f;
        
        // Vignette control
        private Camera playerCamera;
        private GameObject vignetteOverlay;
        private float currentVignetteIntensity = 0f;
        private float targetVignetteIntensity = 0f;
        
        // Snap turning
        private float lastSnapTurnTime;
        private bool snapTurnInputProcessed = false;
        
        // Motion tracking
        private Queue<MotionSample> motionHistory = new Queue<MotionSample>();
        private const int maxMotionSamples = 60; // 1 second at 60fps
        
        // Events
        public System.Action<float> OnComfortScoreChanged;
        public System.Action<bool> OnDiscomfortStateChanged;
        public System.Action OnComfortBreakRequested;
        
        private void Start()
        {
            Initialize();
        }
        
        public void Initialize()
        {
            // Get player camera
            playerCamera = Camera.main;
            if (playerCamera == null)
            {
                playerCamera = FindObjectOfType<Camera>();
            }
            
            // Setup vignette overlay
            if (enableVignetting && playerCamera != null)
            {
                SetupVignetteOverlay();
            }
            
            // Initialize motion tracking
            if (playerCamera != null)
            {
                lastHeadPosition = playerCamera.transform.position;
                lastHeadRotation = playerCamera.transform.rotation;
            }
            
            // Setup UI
            if (comfortUI != null)
            {
                comfortUI.gameObject.SetActive(false);
            }
            
            Debug.Log($"Comfort Manager initialized with comfort level: {comfortLevel}");
        }
        
        private void SetupVignetteOverlay()
        {
            // Create vignette overlay
            vignetteOverlay = new GameObject("VignetteOverlay");
            vignetteOverlay.transform.SetParent(playerCamera.transform);
            vignetteOverlay.transform.localPosition = Vector3.forward * 0.1f; // Just in front of camera
            vignetteOverlay.transform.localRotation = Quaternion.identity;
            vignetteOverlay.transform.localScale = Vector3.one;
            
            // Add quad mesh
            var meshFilter = vignetteOverlay.AddComponent<MeshFilter>();
            var meshRenderer = vignetteOverlay.AddComponent<MeshRenderer>();
            
            // Create quad mesh
            meshFilter.mesh = CreateQuadMesh();
            meshRenderer.material = vignetteMaterial;
            
            // Set initial transparency
            SetVignetteIntensity(0f);
        }
        
        private Mesh CreateQuadMesh()
        {
            var mesh = new Mesh();
            
            Vector3[] vertices = {
                new Vector3(-1, -1, 0),
                new Vector3(1, -1, 0),
                new Vector3(1, 1, 0),
                new Vector3(-1, 1, 0)
            };
            
            int[] triangles = { 0, 2, 1, 0, 3, 2 };
            Vector2[] uvs = {
                new Vector2(0, 0),
                new Vector2(1, 0),
                new Vector2(1, 1),
                new Vector2(0, 1)
            };
            
            mesh.vertices = vertices;
            mesh.triangles = triangles;
            mesh.uv = uvs;
            mesh.RecalculateNormals();
            
            return mesh;
        }
        
        private void Update()
        {
            if (!enableComfortFeatures) return;
            
            UpdateMotionTracking();
            UpdateComfortScore();
            UpdateVignette();
            UpdateSnapTurning();
            UpdateComfortUI();
        }
        
        private void UpdateMotionTracking()
        {
            if (!enableMotionMonitoring || playerCamera == null) return;
            
            Vector3 currentPosition = playerCamera.transform.position;
            Quaternion currentRotation = playerCamera.transform.rotation;
            
            // Calculate motion deltas
            float positionDelta = Vector3.Distance(currentPosition, lastHeadPosition);
            float rotationDelta = Quaternion.Angle(currentRotation, lastHeadRotation);
            
            // Create motion sample
            var sample = new MotionSample
            {
                timestamp = Time.time,
                positionDelta = positionDelta,
                rotationDelta = rotationDelta,
                combinedMotion = positionDelta + (rotationDelta * 0.1f) // Weight rotation less
            };
            
            // Add to history
            motionHistory.Enqueue(sample);
            
            // Remove old samples
            while (motionHistory.Count > maxMotionSamples)
            {
                motionHistory.Dequeue();
            }
            
            // Update accumulated motion
            accumulatedMotion = 0f;
            foreach (var motionSample in motionHistory)
            {
                accumulatedMotion += motionSample.combinedMotion;
            }
            
            // Store current values for next frame
            lastHeadPosition = currentPosition;
            lastHeadRotation = currentRotation;
        }
        
        private void UpdateComfortScore()
        {
            if (!enableMotionMonitoring) return;
            
            // Calculate comfort score based on accumulated motion
            float motionFactor = Mathf.Clamp01(accumulatedMotion / 10f); // Normalize motion
            float targetComfortScore = 1f - motionFactor;
            
            // Apply comfort level modifiers
            targetComfortScore = ApplyComfortLevelModifier(targetComfortScore);
            
            // Smooth comfort score changes
            currentComfortScore = Mathf.Lerp(currentComfortScore, targetComfortScore, Time.deltaTime * 2f);
            
            // Check for discomfort
            bool wasExperiencingDiscomfort = isExperiencingDiscomfort;
            isExperiencingDiscomfort = currentComfortScore < motionSicknessThreshold;
            
            if (isExperiencingDiscomfort && !wasExperiencingDiscomfort)
            {
                discomfortStartTime = Time.time;
                OnDiscomfortStateChanged?.Invoke(true);
                Debug.LogWarning("Motion discomfort detected");
            }
            else if (!isExperiencingDiscomfort && wasExperiencingDiscomfort)
            {
                OnDiscomfortStateChanged?.Invoke(false);
                Debug.Log("Motion comfort restored");
            }
            
            // Trigger comfort break if discomfort persists
            if (isExperiencingDiscomfort && Time.time - discomfortStartTime > recoveryTime)
            {
                RequestComfortBreak();
            }
            
            OnComfortScoreChanged?.Invoke(currentComfortScore);
        }
        
        private float ApplyComfortLevelModifier(float baseScore)
        {
            switch (comfortLevel)
            {
                case ComfortLevel.High:
                    return Mathf.Max(baseScore, 0.7f); // Maintain higher minimum comfort
                case ComfortLevel.Medium:
                    return baseScore;
                case ComfortLevel.Low:
                    return Mathf.Min(baseScore * 1.2f, 1f); // Allow more motion
                default:
                    return baseScore;
            }
        }
        
        private void UpdateVignette()
        {
            if (!enableVignetting || vignetteOverlay == null) return;
            
            // Calculate target vignette intensity based on comfort score
            if (isExperiencingDiscomfort)
            {
                targetVignetteIntensity = vignetteIntensity * (1f - currentComfortScore);
            }
            else
            {
                targetVignetteIntensity = 0f;
            }
            
            // Smooth vignette transition
            currentVignetteIntensity = Mathf.Lerp(
                currentVignetteIntensity, 
                targetVignetteIntensity, 
                Time.deltaTime * vignetteSpeed
            );
            
            SetVignetteIntensity(currentVignetteIntensity);
        }
        
        private void SetVignetteIntensity(float intensity)
        {
            if (vignetteOverlay == null) return;
            
            var renderer = vignetteOverlay.GetComponent<MeshRenderer>();
            if (renderer != null && renderer.material != null)
            {
                Color color = renderer.material.color;
                color.a = intensity;
                renderer.material.color = color;
            }
        }
        
        private void UpdateSnapTurning()
        {
            if (!enableSnapTurning) return;
            
            // Check for snap turn input
            bool snapTurnInput = false;
            float turnDirection = 0f;
            
            // Keyboard input (for testing)
            if (Input.GetKeyDown(KeyCode.Q))
            {
                snapTurnInput = true;
                turnDirection = -1f;
            }
            else if (Input.GetKeyDown(KeyCode.E))
            {
                snapTurnInput = true;
                turnDirection = 1f;
            }
            
            // VR controller input
            if (XRSettings.enabled)
            {
                InputDevice rightController = InputDevices.GetDeviceAtXRNode(XRNode.RightHand);
                if (rightController.TryGetFeatureValue(CommonUsages.primary2DAxis, out Vector2 thumbstick))
                {
                    if (!snapTurnInputProcessed && Mathf.Abs(thumbstick.x) > 0.7f)
                    {
                        snapTurnInput = true;
                        turnDirection = Mathf.Sign(thumbstick.x);
                        snapTurnInputProcessed = true;
                    }
                    else if (Mathf.Abs(thumbstick.x) < 0.3f)
                    {
                        snapTurnInputProcessed = false;
                    }
                }
            }
            
            // Execute snap turn
            if (snapTurnInput && Time.time - lastSnapTurnTime > snapTurnCooldown)
            {
                PerformSnapTurn(turnDirection);
                lastSnapTurnTime = Time.time;
            }
        }
        
        private void PerformSnapTurn(float direction)
        {
            if (playerCamera == null) return;
            
            // Get the player rig (parent of camera)
            Transform playerRig = playerCamera.transform.parent;
            if (playerRig == null)
            {
                playerRig = playerCamera.transform;
            }
            
            // Perform snap turn
            float turnAngle = snapTurnAngle * direction;
            playerRig.Rotate(0, turnAngle, 0);
            
            Debug.Log($"Performed snap turn: {turnAngle} degrees");
        }
        
        private void UpdateComfortUI()
        {
            if (comfortUI == null) return;
            
            // Show UI when experiencing discomfort
            bool shouldShowUI = isExperiencingDiscomfort || currentComfortScore < 0.9f;
            
            if (comfortUI.gameObject.activeSelf != shouldShowUI)
            {
                comfortUI.gameObject.SetActive(shouldShowUI);
            }
            
            if (shouldShowUI)
            {
                // Update comfort slider
                if (comfortSlider != null)
                {
                    comfortSlider.value = currentComfortScore;
                }
                
                // Update comfort text
                if (comfortText != null)
                {
                    string status = currentComfortScore > 0.8f ? "Comfortable" :
                                   currentComfortScore > 0.6f ? "Mild Discomfort" :
                                   currentComfortScore > 0.4f ? "Moderate Discomfort" : "High Discomfort";
                    
                    comfortText.text = $"Comfort: {status} ({currentComfortScore:P0})";
                }
            }
        }
        
        private void RequestComfortBreak()
        {
            Debug.LogWarning("Requesting comfort break due to prolonged discomfort");
            OnComfortBreakRequested?.Invoke();
            
            // Reset discomfort timer
            discomfortStartTime = Time.time;
        }
        
        // Public methods
        public void SetComfortLevel(ComfortLevel level)
        {
            comfortLevel = level;
            Debug.Log($"Comfort level set to: {level}");
        }
        
        public void EnableVignetting(bool enable)
        {
            enableVignetting = enable;
            if (!enable && vignetteOverlay != null)
            {
                SetVignetteIntensity(0f);
            }
        }
        
        public void EnableSnapTurning(bool enable)
        {
            enableSnapTurning = enable;
        }
        
        public void ResetComfortTracking()
        {
            currentComfortScore = 1f;
            isExperiencingDiscomfort = false;
            accumulatedMotion = 0f;
            motionHistory.Clear();
            
            if (vignetteOverlay != null)
            {
                SetVignetteIntensity(0f);
            }
        }
        
        // Public getters
        public float CurrentComfortScore => currentComfortScore;
        public bool IsExperiencingDiscomfort => isExperiencingDiscomfort;
        public ComfortLevel CurrentComfortLevel => comfortLevel;
    }
    
    public enum ComfortLevel
    {
        Low,    // Allow more motion, less comfort features
        Medium, // Balanced comfort features
        High    // Maximum comfort features, minimal motion
    }
    
    [System.Serializable]
    public class MotionSample
    {
        public float timestamp;
        public float positionDelta;
        public float rotationDelta;
        public float combinedMotion;
    }
}
