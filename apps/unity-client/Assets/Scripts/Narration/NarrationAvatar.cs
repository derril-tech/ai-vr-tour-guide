using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

namespace VRTourGuide.Narration
{
    /// <summary>
    /// Animated avatar for tour narration with lip-sync and gestures
    /// Handles TTS playback, viseme animation, and contextual gestures
    /// </summary>
    public class NarrationAvatar : MonoBehaviour
    {
        [Header("Avatar Configuration")]
        [SerializeField] private Animator avatarAnimator;
        [SerializeField] private SkinnedMeshRenderer faceRenderer;
        [SerializeField] private AudioSource audioSource;
        
        [Header("Positioning")]
        [SerializeField] private Transform playerCamera;
        [SerializeField] private float distanceFromPlayer = 2f;
        [SerializeField] private float heightOffset = 0.2f;
        [SerializeField] private bool followPlayer = true;
        [SerializeField] private float followSpeed = 2f;
        
        [Header("Animation")]
        [SerializeField] private float gestureFrequency = 0.3f;
        [SerializeField] private float eyeBlinkFrequency = 3f;
        [SerializeField] private float headMovementIntensity = 0.5f;
        
        [Header("Lip Sync")]
        [SerializeField] private bool enableLipSync = true;
        [SerializeField] private float visemeIntensity = 1f;
        [SerializeField] private AnimationCurve visemeCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);
        
        // Narration state
        private bool isNarrating = false;
        private bool isPaused = false;
        private AudioClip currentNarrationClip;
        private VisemeData currentVisemeData;
        
        // Animation state
        private float lastGestureTime;
        private float lastBlinkTime;
        private int currentGestureIndex = 0;
        
        // Lip sync
        private int currentVisemeIndex = 0;
        private float narrationStartTime;
        
        // Animation parameters
        private readonly int IsNarratingParam = Animator.StringToHash("IsNarrating");
        private readonly int GestureIndexParam = Animator.StringToHash("GestureIndex");
        private readonly int BlinkTriggerParam = Animator.StringToHash("Blink");
        
        // Viseme blend shapes (standard ARKit/Oculus naming)
        private readonly string[] visemeBlendShapes = {
            "viseme_sil", "viseme_PP", "viseme_FF", "viseme_TH",
            "viseme_DD", "viseme_kk", "viseme_CH", "viseme_SS",
            "viseme_nn", "viseme_RR", "viseme_aa", "viseme_E",
            "viseme_I", "viseme_O", "viseme_U"
        };
        
        private void Start()
        {
            Initialize();
        }
        
        public void Initialize()
        {
            // Get player camera if not assigned
            if (playerCamera == null)
            {
                playerCamera = Camera.main?.transform;
            }
            
            // Setup audio source
            if (audioSource == null)
            {
                audioSource = GetComponent<AudioSource>();
                if (audioSource == null)
                {
                    audioSource = gameObject.AddComponent<AudioSource>();
                }
            }
            
            audioSource.spatialBlend = 0.8f; // Mostly 3D audio
            audioSource.rolloffMode = AudioRolloffMode.Linear;
            audioSource.maxDistance = 10f;
            
            // Initialize animation timers
            lastGestureTime = Time.time;
            lastBlinkTime = Time.time;
            
            Debug.Log("Narration Avatar initialized");
        }
        
        public void StartNarration(string text, AudioClip audioClip = null)
        {
            if (string.IsNullOrEmpty(text))
            {
                Debug.LogWarning("Cannot start narration: text is empty");
                return;
            }
            
            StopNarration();
            
            isNarrating = true;
            isPaused = false;
            
            // Set animator state
            if (avatarAnimator != null)
            {
                avatarAnimator.SetBool(IsNarratingParam, true);
            }
            
            if (audioClip != null)
            {
                // Use provided audio clip
                PlayNarrationAudio(audioClip);
            }
            else
            {
                // Generate TTS audio
                StartCoroutine(GenerateTTSAudio(text));
            }
            
            Debug.Log($"Started narration: {text.Substring(0, Mathf.Min(50, text.Length))}...");
        }
        
        public void PauseNarration()
        {
            if (!isNarrating) return;
            
            isPaused = true;
            audioSource.Pause();
            
            if (avatarAnimator != null)
            {
                avatarAnimator.SetBool(IsNarratingParam, false);
            }
        }
        
        public void ResumeNarration()
        {
            if (!isNarrating || !isPaused) return;
            
            isPaused = false;
            audioSource.UnPause();
            
            if (avatarAnimator != null)
            {
                avatarAnimator.SetBool(IsNarratingParam, true);
            }
        }
        
        public void StopNarration()
        {
            isNarrating = false;
            isPaused = false;
            
            audioSource.Stop();
            
            if (avatarAnimator != null)
            {
                avatarAnimator.SetBool(IsNarratingParam, false);
            }
            
            // Reset visemes
            ResetVisemes();
        }
        
        private IEnumerator GenerateTTSAudio(string text)
        {
            // In a real implementation, this would call the TTS service
            // For now, we'll simulate the process
            
            yield return new WaitForSeconds(0.5f); // Simulate API call delay
            
            // Mock TTS response with viseme data
            var mockVisemeData = GenerateMockVisemeData(text);
            currentVisemeData = mockVisemeData;
            
            // For demo purposes, use a placeholder audio clip
            // In production, this would be the actual TTS-generated audio
            var mockAudioClip = GenerateMockAudioClip(text.Length * 0.1f); // ~0.1 seconds per character
            
            PlayNarrationAudio(mockAudioClip);
        }
        
        private void PlayNarrationAudio(AudioClip clip)
        {
            currentNarrationClip = clip;
            audioSource.clip = clip;
            audioSource.Play();
            
            narrationStartTime = Time.time;
            currentVisemeIndex = 0;
            
            // Start lip sync coroutine
            if (enableLipSync && currentVisemeData != null)
            {
                StartCoroutine(PlayVisemeAnimation());
            }
        }
        
        private IEnumerator PlayVisemeAnimation()
        {
            while (isNarrating && !isPaused && audioSource.isPlaying)
            {
                float currentTime = Time.time - narrationStartTime;
                
                // Find current viseme
                if (currentVisemeData != null && currentVisemeIndex < currentVisemeData.visemes.Count)
                {
                    var viseme = currentVisemeData.visemes[currentVisemeIndex];
                    
                    if (currentTime >= viseme.timestamp)
                    {
                        ApplyViseme(viseme.visemeId, viseme.intensity);
                        currentVisemeIndex++;
                    }
                }
                
                yield return null;
            }
            
            // Reset visemes when done
            ResetVisemes();
        }
        
        private void ApplyViseme(int visemeId, float intensity)
        {
            if (faceRenderer == null || visemeId < 0 || visemeId >= visemeBlendShapes.Length)
                return;
            
            // Reset all viseme blend shapes
            for (int i = 0; i < visemeBlendShapes.Length; i++)
            {
                int blendShapeIndex = faceRenderer.sharedMesh.GetBlendShapeIndex(visemeBlendShapes[i]);
                if (blendShapeIndex >= 0)
                {
                    faceRenderer.SetBlendShapeWeight(blendShapeIndex, 0f);
                }
            }
            
            // Apply current viseme
            int targetBlendShapeIndex = faceRenderer.sharedMesh.GetBlendShapeIndex(visemeBlendShapes[visemeId]);
            if (targetBlendShapeIndex >= 0)
            {
                float weight = intensity * visemeIntensity * 100f; // Blend shape weights are 0-100
                weight = visemeCurve.Evaluate(weight / 100f) * 100f;
                faceRenderer.SetBlendShapeWeight(targetBlendShapeIndex, weight);
            }
        }
        
        private void ResetVisemes()
        {
            if (faceRenderer == null) return;
            
            for (int i = 0; i < visemeBlendShapes.Length; i++)
            {
                int blendShapeIndex = faceRenderer.sharedMesh.GetBlendShapeIndex(visemeBlendShapes[i]);
                if (blendShapeIndex >= 0)
                {
                    faceRenderer.SetBlendShapeWeight(blendShapeIndex, 0f);
                }
            }
        }
        
        private void Update()
        {
            UpdatePositioning();
            UpdateGestures();
            UpdateEyeBlinks();
            UpdateHeadMovement();
        }
        
        private void UpdatePositioning()
        {
            if (!followPlayer || playerCamera == null) return;
            
            // Calculate target position
            Vector3 targetPosition = playerCamera.position + playerCamera.forward * distanceFromPlayer;
            targetPosition.y += heightOffset;
            
            // Smooth follow
            transform.position = Vector3.Lerp(transform.position, targetPosition, followSpeed * Time.deltaTime);
            
            // Look at player
            Vector3 lookDirection = (playerCamera.position - transform.position).normalized;
            lookDirection.y = 0; // Keep avatar upright
            
            if (lookDirection != Vector3.zero)
            {
                Quaternion targetRotation = Quaternion.LookRotation(lookDirection);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, followSpeed * Time.deltaTime);
            }
        }
        
        private void UpdateGestures()
        {
            if (!isNarrating || isPaused || avatarAnimator == null) return;
            
            // Trigger gestures periodically during narration
            if (Time.time - lastGestureTime > (1f / gestureFrequency))
            {
                TriggerRandomGesture();
                lastGestureTime = Time.time;
            }
        }
        
        private void TriggerRandomGesture()
        {
            // Cycle through available gestures
            currentGestureIndex = (currentGestureIndex + 1) % 5; // Assuming 5 gesture animations
            avatarAnimator.SetInteger(GestureIndexParam, currentGestureIndex);
            avatarAnimator.SetTrigger("TriggerGesture");
        }
        
        private void UpdateEyeBlinks()
        {
            if (avatarAnimator == null) return;
            
            // Trigger eye blinks periodically
            if (Time.time - lastBlinkTime > (1f / eyeBlinkFrequency))
            {
                avatarAnimator.SetTrigger(BlinkTriggerParam);
                lastBlinkTime = Time.time + Random.Range(-0.5f, 0.5f); // Add some randomness
            }
        }
        
        private void UpdateHeadMovement()
        {
            if (!isNarrating || avatarAnimator == null) return;
            
            // Subtle head movement during narration
            float headX = Mathf.Sin(Time.time * 0.5f) * headMovementIntensity;
            float headY = Mathf.Cos(Time.time * 0.3f) * headMovementIntensity * 0.5f;
            
            avatarAnimator.SetFloat("HeadX", headX);
            avatarAnimator.SetFloat("HeadY", headY);
        }
        
        // Mock data generation for demo purposes
        private VisemeData GenerateMockVisemeData(string text)
        {
            var visemeData = new VisemeData();
            visemeData.visemes = new List<VisemeFrame>();
            
            // Generate mock visemes based on text length
            float duration = text.Length * 0.08f; // ~80ms per character
            int visemeCount = Mathf.RoundToInt(duration * 10); // ~10 visemes per second
            
            for (int i = 0; i < visemeCount; i++)
            {
                var viseme = new VisemeFrame
                {
                    timestamp = (float)i / 10f,
                    visemeId = Random.Range(0, visemeBlendShapes.Length),
                    intensity = Random.Range(0.3f, 1f)
                };
                visemeData.visemes.Add(viseme);
            }
            
            return visemeData;
        }
        
        private AudioClip GenerateMockAudioClip(float duration)
        {
            // Generate a simple sine wave for demo purposes
            int sampleRate = 44100;
            int samples = Mathf.RoundToInt(sampleRate * duration);
            float[] audioData = new float[samples];
            
            for (int i = 0; i < samples; i++)
            {
                float t = (float)i / sampleRate;
                audioData[i] = Mathf.Sin(2 * Mathf.PI * 440 * t) * 0.1f; // 440Hz sine wave
            }
            
            var clip = AudioClip.Create("MockTTS", samples, 1, sampleRate, false);
            clip.SetData(audioData, 0);
            return clip;
        }
        
        // Public getters
        public bool IsNarrating => isNarrating;
        public bool IsPaused => isPaused;
        public float NarrationProgress => currentNarrationClip != null ? audioSource.time / currentNarrationClip.length : 0f;
    }
    
    [System.Serializable]
    public class VisemeData
    {
        public List<VisemeFrame> visemes = new List<VisemeFrame>();
    }
    
    [System.Serializable]
    public class VisemeFrame
    {
        public float timestamp;
        public int visemeId;
        public float intensity;
    }
}
