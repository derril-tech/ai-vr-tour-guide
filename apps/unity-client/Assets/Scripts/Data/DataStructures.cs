using System.Collections.Generic;
using UnityEngine;

namespace VRTourGuide.Data
{
    /// <summary>
    /// Core data structures for the VR Tour Guide Unity client
    /// </summary>
    
    [System.Serializable]
    public class TourData
    {
        public string id;
        public string title;
        public string description;
        public List<TourStep> steps = new List<TourStep>();
        public TourMetadata metadata;
    }
    
    [System.Serializable]
    public class TourStep
    {
        public string id;
        public string title;
        public string description;
        public Vector3 playerPosition;
        public Quaternion playerRotation;
        public string narrationText;
        public AudioClip narrationAudio;
        public List<SceneObjectData> sceneObjects = new List<SceneObjectData>();
        public List<Hotspot> hotspots = new List<Hotspot>();
        public List<OverlayData> overlays = new List<OverlayData>();
        public LightingSettings lightingSettings;
        public EnvironmentSettings environmentSettings;
    }
    
    [System.Serializable]
    public class SceneObjectData
    {
        public string id;
        public string name;
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 scale = Vector3.one;
        public string addressableKey;
        public string assetPath;
        public bool useLOD = true;
        public int priority = 0;
        public List<MaterialOverride> materialOverrides = new List<MaterialOverride>();
    }
    
    [System.Serializable]
    public class MaterialOverride
    {
        public int materialSlot;
        public Material material;
    }
    
    [System.Serializable]
    public class Hotspot
    {
        public string id;
        public string title;
        public string content;
        public HotspotType type;
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 scale = Vector3.one;
        public float visibilityRange = 10f;
        public float visibilityAngle = 60f;
        public bool requiresLineOfSight = false;
        public int targetStepIndex = -1;
        public QuizData quizData;
        public System.Action interactionCallback;
    }
    
    public enum HotspotType
    {
        Information,
        Navigation,
        Interactive,
        Quiz
    }
    
    [System.Serializable]
    public class OverlayData
    {
        public string id;
        public string title;
        public string content;
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 scale = Vector3.one;
    }
    
    [System.Serializable]
    public class QuizData
    {
        public string id;
        public string title;
        public string question;
        public List<string> answers = new List<string>();
        public int correctAnswerIndex;
        public string explanation;
    }
    
    [System.Serializable]
    public class QuizResult
    {
        public string quizId;
        public int selectedAnswer;
        public bool isCorrect;
        public float timeToAnswer;
    }
    
    [System.Serializable]
    public class CitationData
    {
        public string id;
        public string title;
        public string source;
        public string url;
        public string excerpt;
    }
    
    [System.Serializable]
    public class LightingSettings
    {
        public Color ambientColor = Color.gray;
        public float ambientIntensity = 1f;
        public Color sunColor = Color.white;
        public float sunIntensity = 1f;
        public Vector3 sunRotation = new Vector3(50f, -30f, 0f);
        public Material skyboxMaterial;
    }
    
    [System.Serializable]
    public class EnvironmentSettings
    {
        public bool enableFog = false;
        public Color fogColor = Color.gray;
        public FogMode fogMode = FogMode.Linear;
        public float fogStart = 10f;
        public float fogEnd = 100f;
        public WindZone windZone;
        public float windStrength = 0.5f;
        public float windTurbulence = 0.1f;
    }
    
    [System.Serializable]
    public class TourMetadata
    {
        public string author;
        public string version;
        public System.DateTime createdDate;
        public System.DateTime lastModified;
        public List<string> tags = new List<string>();
        public float estimatedDuration; // in minutes
        public string difficulty; // "Easy", "Medium", "Hard"
    }
}
