using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace VRTourGuide.Overlays
{
    /// <summary>
    /// Manages AR/VR overlays and UI elements in world space
    /// Handles information panels, quizzes, and contextual UI
    /// </summary>
    public class OverlayManager : MonoBehaviour
    {
        [Header("Overlay Prefabs")]
        [SerializeField] private GameObject informationOverlayPrefab;
        [SerializeField] private GameObject quizOverlayPrefab;
        [SerializeField] private GameObject completionOverlayPrefab;
        [SerializeField] private GameObject citationOverlayPrefab;
        
        [Header("Positioning")]
        [SerializeField] private Transform playerCamera;
        [SerializeField] private float overlayDistance = 2f;
        [SerializeField] private float overlayHeight = 0.5f;
        [SerializeField] private bool followPlayerGaze = true;
        
        [Header("Animation")]
        [SerializeField] private float fadeInDuration = 0.5f;
        [SerializeField] private float fadeOutDuration = 0.3f;
        [SerializeField] private AnimationCurve fadeCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);
        
        // Overlay management
        private Dictionary<string, OverlayController> activeOverlays = new Dictionary<string, OverlayController>();
        private Transform overlaysParent;
        private Queue<OverlayRequest> overlayQueue = new Queue<OverlayRequest>();
        private bool isShowingOverlay = false;
        
        // Events
        public System.Action<string> OnOverlayShown;
        public System.Action<string> OnOverlayHidden;
        public System.Action<QuizResult> OnQuizCompleted;
        
        private void Start()
        {
            Initialize();
        }
        
        private void Initialize()
        {
            // Create overlays parent
            overlaysParent = new GameObject("Overlays").transform;
            overlaysParent.SetParent(transform);
            
            // Get player camera
            if (playerCamera == null)
            {
                playerCamera = Camera.main?.transform;
            }
            
            Debug.Log("Overlay Manager initialized");
        }
        
        public void ShowInformationOverlay(string content, string title = "Information")
        {
            var request = new OverlayRequest
            {
                type = OverlayType.Information,
                content = content,
                title = title,
                duration = 0f // Persistent until dismissed
            };
            
            QueueOverlay(request);
        }
        
        public void ShowQuizOverlay(QuizData quiz)
        {
            var request = new OverlayRequest
            {
                type = OverlayType.Quiz,
                quizData = quiz,
                title = quiz.title,
                duration = 0f // Persistent until completed
            };
            
            QueueOverlay(request);
        }
        
        public void ShowCompletionOverlay(TourData tour)
        {
            var request = new OverlayRequest
            {
                type = OverlayType.Completion,
                tourData = tour,
                title = "Tour Complete!",
                duration = 5f // Auto-dismiss after 5 seconds
            };
            
            QueueOverlay(request);
        }
        
        public void ShowCitationOverlay(CitationData citation, Vector3 worldPosition)
        {
            var request = new OverlayRequest
            {
                type = OverlayType.Citation,
                citationData = citation,
                title = citation.title,
                worldPosition = worldPosition,
                useWorldPosition = true,
                duration = 3f // Auto-dismiss after 3 seconds
            };
            
            QueueOverlay(request);
        }
        
        private void QueueOverlay(OverlayRequest request)
        {
            overlayQueue.Enqueue(request);
            ProcessOverlayQueue();
        }
        
        private void ProcessOverlayQueue()
        {
            if (isShowingOverlay || overlayQueue.Count == 0) return;
            
            var request = overlayQueue.Dequeue();
            StartCoroutine(ShowOverlayCoroutine(request));
        }
        
        private IEnumerator ShowOverlayCoroutine(OverlayRequest request)
        {
            isShowingOverlay = true;
            
            // Create overlay
            GameObject overlayPrefab = GetOverlayPrefab(request.type);
            if (overlayPrefab == null)
            {
                Debug.LogError($"No prefab found for overlay type: {request.type}");
                isShowingOverlay = false;
                yield break;
            }
            
            GameObject overlayObj = Instantiate(overlayPrefab, overlaysParent);
            overlayObj.name = $"Overlay_{request.type}_{System.Guid.NewGuid().ToString("N")[..8]}";
            
            // Position overlay
            PositionOverlay(overlayObj, request);
            
            // Setup overlay controller
            var controller = overlayObj.GetComponent<OverlayController>();
            if (controller == null)
            {
                controller = overlayObj.AddComponent<OverlayController>();
            }
            
            controller.Initialize(request, this);
            
            // Add to active overlays
            activeOverlays[overlayObj.name] = controller;
            
            // Animate in
            yield return StartCoroutine(AnimateOverlay(controller, true));
            
            OnOverlayShown?.Invoke(overlayObj.name);
            
            // Auto-dismiss if duration is set
            if (request.duration > 0f)
            {
                yield return new WaitForSeconds(request.duration);
                HideOverlay(overlayObj.name);
            }
            
            isShowingOverlay = false;
            ProcessOverlayQueue();
        }
        
        private GameObject GetOverlayPrefab(OverlayType type)
        {
            switch (type)
            {
                case OverlayType.Information:
                    return informationOverlayPrefab;
                case OverlayType.Quiz:
                    return quizOverlayPrefab;
                case OverlayType.Completion:
                    return completionOverlayPrefab;
                case OverlayType.Citation:
                    return citationOverlayPrefab;
                default:
                    return informationOverlayPrefab;
            }
        }
        
        private void PositionOverlay(GameObject overlay, OverlayRequest request)
        {
            if (request.useWorldPosition)
            {
                overlay.transform.position = request.worldPosition;
            }
            else if (playerCamera != null)
            {
                // Position in front of player
                Vector3 position = playerCamera.position + playerCamera.forward * overlayDistance;
                position.y += overlayHeight;
                overlay.transform.position = position;
                
                // Face the player
                Vector3 lookDirection = (playerCamera.position - overlay.transform.position).normalized;
                overlay.transform.rotation = Quaternion.LookRotation(-lookDirection);
            }
        }
        
        public void HideOverlay(string overlayId)
        {
            if (activeOverlays.TryGetValue(overlayId, out OverlayController controller))
            {
                StartCoroutine(HideOverlayCoroutine(overlayId, controller));
            }
        }
        
        private IEnumerator HideOverlayCoroutine(string overlayId, OverlayController controller)
        {
            // Animate out
            yield return StartCoroutine(AnimateOverlay(controller, false));
            
            // Remove from active overlays
            activeOverlays.Remove(overlayId);
            
            // Destroy overlay
            if (controller != null && controller.gameObject != null)
            {
                Destroy(controller.gameObject);
            }
            
            OnOverlayHidden?.Invoke(overlayId);
        }
        
        private IEnumerator AnimateOverlay(OverlayController controller, bool fadeIn)
        {
            if (controller == null) yield break;
            
            float duration = fadeIn ? fadeInDuration : fadeOutDuration;
            float startAlpha = fadeIn ? 0f : 1f;
            float endAlpha = fadeIn ? 1f : 0f;
            
            Vector3 startScale = fadeIn ? Vector3.zero : Vector3.one;
            Vector3 endScale = fadeIn ? Vector3.one : Vector3.zero;
            
            float elapsed = 0f;
            
            while (elapsed < duration)
            {
                float t = elapsed / duration;
                float curveT = fadeCurve.Evaluate(t);
                
                // Animate alpha
                float alpha = Mathf.Lerp(startAlpha, endAlpha, curveT);
                controller.SetAlpha(alpha);
                
                // Animate scale
                Vector3 scale = Vector3.Lerp(startScale, endScale, curveT);
                controller.transform.localScale = scale;
                
                elapsed += Time.deltaTime;
                yield return null;
            }
            
            // Ensure final values
            controller.SetAlpha(endAlpha);
            controller.transform.localScale = endScale;
        }
        
        public void ClearOverlays()
        {
            // Clear queue
            overlayQueue.Clear();
            
            // Hide all active overlays
            var overlayIds = new List<string>(activeOverlays.Keys);
            foreach (var id in overlayIds)
            {
                HideOverlay(id);
            }
        }
        
        public void LoadOverlays(List<OverlayData> overlays)
        {
            foreach (var overlayData in overlays)
            {
                CreateStaticOverlay(overlayData);
            }
        }
        
        private void CreateStaticOverlay(OverlayData overlayData)
        {
            var request = new OverlayRequest
            {
                type = OverlayType.Information,
                content = overlayData.content,
                title = overlayData.title,
                worldPosition = overlayData.position,
                useWorldPosition = true,
                duration = 0f // Persistent
            };
            
            // Create immediately without queueing
            StartCoroutine(ShowOverlayCoroutine(request));
        }
        
        private void Update()
        {
            UpdateOverlayPositions();
        }
        
        private void UpdateOverlayPositions()
        {
            if (!followPlayerGaze || playerCamera == null) return;
            
            foreach (var controller in activeOverlays.Values)
            {
                if (controller != null && !controller.UseWorldPosition)
                {
                    // Update position to follow player gaze
                    Vector3 targetPosition = playerCamera.position + playerCamera.forward * overlayDistance;
                    targetPosition.y += overlayHeight;
                    
                    controller.transform.position = Vector3.Lerp(
                        controller.transform.position, 
                        targetPosition, 
                        Time.deltaTime * 2f
                    );
                    
                    // Update rotation to face player
                    Vector3 lookDirection = (playerCamera.position - controller.transform.position).normalized;
                    Quaternion targetRotation = Quaternion.LookRotation(-lookDirection);
                    controller.transform.rotation = Quaternion.Slerp(
                        controller.transform.rotation, 
                        targetRotation, 
                        Time.deltaTime * 3f
                    );
                }
            }
        }
        
        // Event handlers
        public void OnQuizAnswered(QuizResult result)
        {
            OnQuizCompleted?.Invoke(result);
        }
    }
    
    /// <summary>
    /// Individual overlay controller
    /// </summary>
    public class OverlayController : MonoBehaviour
    {
        private OverlayRequest overlayRequest;
        private OverlayManager manager;
        private CanvasGroup canvasGroup;
        
        public bool UseWorldPosition { get; private set; }
        
        public void Initialize(OverlayRequest request, OverlayManager mgr)
        {
            overlayRequest = request;
            manager = mgr;
            UseWorldPosition = request.useWorldPosition;
            
            // Setup canvas group for alpha control
            canvasGroup = GetComponent<CanvasGroup>();
            if (canvasGroup == null)
            {
                canvasGroup = gameObject.AddComponent<CanvasGroup>();
            }
            
            // Setup content based on overlay type
            SetupOverlayContent();
        }
        
        private void SetupOverlayContent()
        {
            switch (overlayRequest.type)
            {
                case OverlayType.Information:
                    SetupInformationOverlay();
                    break;
                case OverlayType.Quiz:
                    SetupQuizOverlay();
                    break;
                case OverlayType.Completion:
                    SetupCompletionOverlay();
                    break;
                case OverlayType.Citation:
                    SetupCitationOverlay();
                    break;
            }
        }
        
        private void SetupInformationOverlay()
        {
            var titleText = GetComponentInChildren<TextMeshProUGUI>();
            if (titleText != null)
            {
                titleText.text = overlayRequest.title;
            }
            
            var contentTexts = GetComponentsInChildren<TextMeshProUGUI>();
            if (contentTexts.Length > 1)
            {
                contentTexts[1].text = overlayRequest.content;
            }
        }
        
        private void SetupQuizOverlay()
        {
            // Setup quiz UI elements
            var quiz = overlayRequest.quizData;
            if (quiz == null) return;
            
            var titleText = GetComponentInChildren<TextMeshProUGUI>();
            if (titleText != null)
            {
                titleText.text = quiz.title;
            }
            
            // Setup question and answers
            // This would be implemented based on the specific quiz UI prefab
        }
        
        private void SetupCompletionOverlay()
        {
            var tour = overlayRequest.tourData;
            if (tour == null) return;
            
            var titleText = GetComponentInChildren<TextMeshProUGUI>();
            if (titleText != null)
            {
                titleText.text = $"Congratulations! You completed: {tour.title}";
            }
        }
        
        private void SetupCitationOverlay()
        {
            var citation = overlayRequest.citationData;
            if (citation == null) return;
            
            var titleText = GetComponentInChildren<TextMeshProUGUI>();
            if (titleText != null)
            {
                titleText.text = citation.title;
            }
            
            var contentTexts = GetComponentsInChildren<TextMeshProUGUI>();
            if (contentTexts.Length > 1)
            {
                contentTexts[1].text = citation.source;
            }
        }
        
        public void SetAlpha(float alpha)
        {
            if (canvasGroup != null)
            {
                canvasGroup.alpha = alpha;
            }
        }
        
        public void OnCloseButtonClicked()
        {
            if (manager != null)
            {
                manager.HideOverlay(gameObject.name);
            }
        }
    }
    
    // Data structures
    public enum OverlayType
    {
        Information,
        Quiz,
        Completion,
        Citation
    }
    
    [System.Serializable]
    public class OverlayRequest
    {
        public OverlayType type;
        public string title;
        public string content;
        public QuizData quizData;
        public TourData tourData;
        public CitationData citationData;
        public Vector3 worldPosition;
        public bool useWorldPosition;
        public float duration;
    }
}
