using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;

namespace VRTourGuide.Core
{
    /// <summary>
    /// Main manager for VR tour experiences
    /// Handles scene loading, tour progression, and user interactions
    /// </summary>
    public class VRTourManager : MonoBehaviour
    {
        [Header("Tour Configuration")]
        [SerializeField] private TourData currentTour;
        [SerializeField] private Transform playerRig;
        [SerializeField] private Camera vrCamera;
        
        [Header("Scene Management")]
        [SerializeField] private SceneGraphManager sceneGraph;
        [SerializeField] private HotspotManager hotspotManager;
        [SerializeField] private OverlayManager overlayManager;
        
        [Header("Narration")]
        [SerializeField] private NarrationAvatar narrator;
        [SerializeField] private AudioSource narratorAudio;
        
        [Header("Comfort & Safety")]
        [SerializeField] private ComfortManager comfortManager;
        [SerializeField] private TeleportationProvider teleportProvider;
        
        [Header("UI")]
        [SerializeField] private Canvas vrUI;
        [SerializeField] private GameObject menuPanel;
        [SerializeField] private GameObject progressPanel;
        
        // Tour state
        private int currentStepIndex = 0;
        private bool tourActive = false;
        private bool isPaused = false;
        
        // Events
        public System.Action<int> OnTourStepChanged;
        public System.Action<bool> OnTourStateChanged;
        public System.Action<string> OnNarrationStarted;
        
        private void Start()
        {
            InitializeVRTour();
        }
        
        private void InitializeVRTour()
        {
            // Initialize VR systems
            if (!XRSettings.enabled)
            {
                Debug.LogWarning("VR not enabled. Tour will run in desktop mode.");
            }
            
            // Setup comfort settings
            comfortManager.Initialize();
            
            // Initialize scene graph
            sceneGraph.Initialize();
            
            // Setup hotspot interactions
            hotspotManager.OnHotspotActivated += HandleHotspotActivation;
            
            // Initialize narrator
            narrator.Initialize();
            
            Debug.Log("VR Tour Manager initialized successfully");
        }
        
        public void StartTour(TourData tour)
        {
            if (tour == null)
            {
                Debug.LogError("Cannot start tour: TourData is null");
                return;
            }
            
            currentTour = tour;
            currentStepIndex = 0;
            tourActive = true;
            isPaused = false;
            
            // Load initial scene
            LoadTourStep(0);
            
            OnTourStateChanged?.Invoke(true);
            Debug.Log($"Started tour: {tour.title}");
        }
        
        public void PauseTour()
        {
            isPaused = true;
            narrator.PauseNarration();
            OnTourStateChanged?.Invoke(false);
        }
        
        public void ResumeTour()
        {
            isPaused = false;
            narrator.ResumeNarration();
            OnTourStateChanged?.Invoke(true);
        }
        
        public void StopTour()
        {
            tourActive = false;
            isPaused = false;
            narrator.StopNarration();
            
            // Clear scene
            sceneGraph.ClearScene();
            hotspotManager.ClearHotspots();
            overlayManager.ClearOverlays();
            
            OnTourStateChanged?.Invoke(false);
            Debug.Log("Tour stopped");
        }
        
        public void NextStep()
        {
            if (!tourActive || isPaused) return;
            
            if (currentStepIndex < currentTour.steps.Count - 1)
            {
                currentStepIndex++;
                LoadTourStep(currentStepIndex);
            }
            else
            {
                // Tour completed
                CompleteTour();
            }
        }
        
        public void PreviousStep()
        {
            if (!tourActive || isPaused) return;
            
            if (currentStepIndex > 0)
            {
                currentStepIndex--;
                LoadTourStep(currentStepIndex);
            }
        }
        
        public void JumpToStep(int stepIndex)
        {
            if (!tourActive || stepIndex < 0 || stepIndex >= currentTour.steps.Count)
                return;
            
            currentStepIndex = stepIndex;
            LoadTourStep(currentStepIndex);
        }
        
        private void LoadTourStep(int stepIndex)
        {
            if (currentTour == null || stepIndex >= currentTour.steps.Count)
                return;
            
            var step = currentTour.steps[stepIndex];
            
            // Load scene elements
            sceneGraph.LoadStep(step);
            
            // Position player
            if (step.playerPosition != Vector3.zero)
            {
                PositionPlayer(step.playerPosition, step.playerRotation);
            }
            
            // Setup hotspots
            hotspotManager.LoadHotspots(step.hotspots);
            
            // Setup overlays
            overlayManager.LoadOverlays(step.overlays);
            
            // Start narration
            if (!string.IsNullOrEmpty(step.narrationText))
            {
                narrator.StartNarration(step.narrationText, step.narrationAudio);
                OnNarrationStarted?.Invoke(step.narrationText);
            }
            
            // Update progress
            UpdateProgress();
            
            OnTourStepChanged?.Invoke(stepIndex);
            Debug.Log($"Loaded tour step {stepIndex + 1}/{currentTour.steps.Count}: {step.title}");
        }
        
        private void PositionPlayer(Vector3 position, Quaternion rotation)
        {
            // Use teleportation for comfort
            if (teleportProvider != null)
            {
                teleportProvider.QueueTeleportRequest(new TeleportRequest
                {
                    destinationPosition = position,
                    destinationRotation = rotation
                });
            }
            else
            {
                // Direct positioning as fallback
                playerRig.position = position;
                playerRig.rotation = rotation;
            }
        }
        
        private void HandleHotspotActivation(Hotspot hotspot)
        {
            Debug.Log($"Hotspot activated: {hotspot.title}");
            
            // Handle different hotspot types
            switch (hotspot.type)
            {
                case HotspotType.Information:
                    ShowInformationPanel(hotspot.content);
                    break;
                case HotspotType.Navigation:
                    JumpToStep(hotspot.targetStepIndex);
                    break;
                case HotspotType.Interactive:
                    TriggerInteraction(hotspot);
                    break;
                case HotspotType.Quiz:
                    ShowQuiz(hotspot.quizData);
                    break;
            }
        }
        
        private void ShowInformationPanel(string content)
        {
            // Show information overlay
            overlayManager.ShowInformationOverlay(content);
        }
        
        private void TriggerInteraction(Hotspot hotspot)
        {
            // Handle interactive elements
            if (hotspot.interactionCallback != null)
            {
                hotspot.interactionCallback.Invoke();
            }
        }
        
        private void ShowQuiz(QuizData quiz)
        {
            // Show quiz interface
            overlayManager.ShowQuizOverlay(quiz);
        }
        
        private void CompleteTour()
        {
            Debug.Log("Tour completed!");
            
            // Show completion screen
            overlayManager.ShowCompletionOverlay(currentTour);
            
            // Stop tour after delay
            StartCoroutine(DelayedTourStop(3f));
        }
        
        private IEnumerator DelayedTourStop(float delay)
        {
            yield return new WaitForSeconds(delay);
            StopTour();
        }
        
        private void UpdateProgress()
        {
            if (progressPanel != null && currentTour != null)
            {
                float progress = (float)(currentStepIndex + 1) / currentTour.steps.Count;
                // Update progress UI
                var progressBar = progressPanel.GetComponentInChildren<UnityEngine.UI.Slider>();
                if (progressBar != null)
                {
                    progressBar.value = progress;
                }
            }
        }
        
        // Input handling
        private void Update()
        {
            HandleVRInput();
        }
        
        private void HandleVRInput()
        {
            // Handle VR controller input
            if (tourActive && !isPaused)
            {
                // Check for menu button
                if (Input.GetKeyDown(KeyCode.Escape) || 
                    (XRSettings.enabled && InputDevices.GetDeviceAtXRNode(XRNode.RightHand).TryGetFeatureValue(CommonUsages.menuButton, out bool menuPressed) && menuPressed))
                {
                    ToggleMenu();
                }
                
                // Check for next/previous step
                if (Input.GetKeyDown(KeyCode.RightArrow))
                {
                    NextStep();
                }
                else if (Input.GetKeyDown(KeyCode.LeftArrow))
                {
                    PreviousStep();
                }
            }
        }
        
        private void ToggleMenu()
        {
            if (menuPanel != null)
            {
                bool isActive = menuPanel.activeSelf;
                menuPanel.SetActive(!isActive);
                
                if (!isActive)
                {
                    PauseTour();
                }
                else
                {
                    ResumeTour();
                }
            }
        }
        
        // Public getters
        public bool IsTourActive => tourActive;
        public bool IsPaused => isPaused;
        public int CurrentStepIndex => currentStepIndex;
        public TourData CurrentTour => currentTour;
        public float TourProgress => currentTour != null ? (float)(currentStepIndex + 1) / currentTour.steps.Count : 0f;
    }
}
