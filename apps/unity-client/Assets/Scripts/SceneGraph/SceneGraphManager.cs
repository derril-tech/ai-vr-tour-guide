using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace VRTourGuide.SceneGraph
{
    /// <summary>
    /// Manages dynamic scene loading and 3D asset management
    /// Handles LOD, occlusion culling, and performance optimization
    /// </summary>
    public class SceneGraphManager : MonoBehaviour
    {
        [Header("Scene Configuration")]
        [SerializeField] private Transform sceneRoot;
        [SerializeField] private Camera mainCamera;
        
        [Header("Performance Settings")]
        [SerializeField] private int maxConcurrentLoads = 3;
        [SerializeField] private float lodDistance1 = 50f;
        [SerializeField] private float lodDistance2 = 100f;
        [SerializeField] private float cullingDistance = 200f;
        
        [Header("Asset Management")]
        [SerializeField] private AssetReferenceGameObject[] preloadedAssets;
        
        // Scene state
        private Dictionary<string, GameObject> loadedObjects = new Dictionary<string, GameObject>();
        private Dictionary<string, AsyncOperationHandle<GameObject>> loadingOperations = new Dictionary<string, AsyncOperationHandle<GameObject>>();
        private Queue<SceneLoadRequest> loadQueue = new Queue<SceneLoadRequest>();
        private int currentLoadCount = 0;
        
        // LOD system
        private Dictionary<GameObject, LODGroup> lodGroups = new Dictionary<GameObject, LODGroup>();
        private List<GameObject> activeObjects = new List<GameObject>();
        
        // Occlusion culling
        private Camera occlusionCamera;
        private Plane[] cameraFrustum = new Plane[6];
        
        private void Start()
        {
            Initialize();
        }
        
        public void Initialize()
        {
            // Setup occlusion camera
            if (mainCamera != null)
            {
                occlusionCamera = mainCamera;
            }
            
            // Preload essential assets
            StartCoroutine(PreloadAssets());
            
            // Start LOD and culling updates
            InvokeRepeating(nameof(UpdateLODAndCulling), 1f, 0.1f);
            
            Debug.Log("Scene Graph Manager initialized");
        }
        
        private IEnumerator PreloadAssets()
        {
            foreach (var assetRef in preloadedAssets)
            {
                if (assetRef != null)
                {
                    var handle = assetRef.LoadAssetAsync<GameObject>();
                    yield return handle;
                    
                    if (handle.Status == AsyncOperationStatus.Succeeded)
                    {
                        Debug.Log($"Preloaded asset: {assetRef.AssetGUID}");
                    }
                }
            }
        }
        
        public void LoadStep(TourStep step)
        {
            // Clear previous step objects (except persistent ones)
            ClearNonPersistentObjects();
            
            // Load new objects for this step
            foreach (var sceneObject in step.sceneObjects)
            {
                LoadSceneObject(sceneObject);
            }
            
            // Update lighting
            UpdateLighting(step.lightingSettings);
            
            // Update environment
            UpdateEnvironment(step.environmentSettings);
        }
        
        public void LoadSceneObject(SceneObjectData objectData)
        {
            if (loadedObjects.ContainsKey(objectData.id))
            {
                // Object already loaded, just update transform
                UpdateObjectTransform(objectData);
                return;
            }
            
            // Queue for loading
            var request = new SceneLoadRequest
            {
                objectData = objectData,
                priority = objectData.priority
            };
            
            loadQueue.Enqueue(request);
            ProcessLoadQueue();
        }
        
        private void ProcessLoadQueue()
        {
            while (loadQueue.Count > 0 && currentLoadCount < maxConcurrentLoads)
            {
                var request = loadQueue.Dequeue();
                StartCoroutine(LoadObjectAsync(request));
            }
        }
        
        private IEnumerator LoadObjectAsync(SceneLoadRequest request)
        {
            currentLoadCount++;
            var objectData = request.objectData;
            
            // Load asset
            AsyncOperationHandle<GameObject> handle;
            
            if (!string.IsNullOrEmpty(objectData.addressableKey))
            {
                handle = Addressables.LoadAssetAsync<GameObject>(objectData.addressableKey);
            }
            else if (!string.IsNullOrEmpty(objectData.assetPath))
            {
                var asset = Resources.Load<GameObject>(objectData.assetPath);
                handle = Addressables.ResourceManager.CreateCompletedOperation(asset, null);
            }
            else
            {
                Debug.LogError($"No valid asset reference for object: {objectData.id}");
                currentLoadCount--;
                yield break;
            }
            
            loadingOperations[objectData.id] = handle;
            yield return handle;
            
            if (handle.Status == AsyncOperationStatus.Succeeded)
            {
                // Instantiate object
                var instance = Instantiate(handle.Result, sceneRoot);
                instance.name = objectData.id;
                
                // Apply transform
                ApplyTransform(instance, objectData);
                
                // Setup LOD
                SetupLOD(instance, objectData);
                
                // Setup materials
                SetupMaterials(instance, objectData);
                
                // Add to loaded objects
                loadedObjects[objectData.id] = instance;
                activeObjects.Add(instance);
                
                Debug.Log($"Loaded scene object: {objectData.id}");
            }
            else
            {
                Debug.LogError($"Failed to load scene object: {objectData.id}");
            }
            
            loadingOperations.Remove(objectData.id);
            currentLoadCount--;
            
            // Process next in queue
            ProcessLoadQueue();
        }
        
        private void ApplyTransform(GameObject obj, SceneObjectData data)
        {
            obj.transform.position = data.position;
            obj.transform.rotation = data.rotation;
            obj.transform.localScale = data.scale;
        }
        
        private void SetupLOD(GameObject obj, SceneObjectData data)
        {
            // Add LOD group if not present
            var lodGroup = obj.GetComponent<LODGroup>();
            if (lodGroup == null && data.useLOD)
            {
                lodGroup = obj.AddComponent<LODGroup>();
                
                // Setup LOD levels
                var renderers = obj.GetComponentsInChildren<Renderer>();
                if (renderers.Length > 0)
                {
                    var lods = new LOD[3];
                    
                    // LOD 0 - High quality (0-50m)
                    lods[0] = new LOD(0.5f, renderers);
                    
                    // LOD 1 - Medium quality (50-100m)
                    var mediumRenderers = GetLODRenderers(obj, 1);
                    lods[1] = new LOD(0.25f, mediumRenderers);
                    
                    // LOD 2 - Low quality (100m+)
                    var lowRenderers = GetLODRenderers(obj, 2);
                    lods[2] = new LOD(0.1f, lowRenderers);
                    
                    lodGroup.SetLODs(lods);
                    lodGroup.RecalculateBounds();
                }
            }
            
            if (lodGroup != null)
            {
                lodGroups[obj] = lodGroup;
            }
        }
        
        private Renderer[] GetLODRenderers(GameObject obj, int lodLevel)
        {
            // In a real implementation, this would return appropriate renderers for each LOD level
            // For now, return all renderers (would be replaced with actual LOD meshes)
            return obj.GetComponentsInChildren<Renderer>();
        }
        
        private void SetupMaterials(GameObject obj, SceneObjectData data)
        {
            if (data.materialOverrides != null && data.materialOverrides.Count > 0)
            {
                var renderers = obj.GetComponentsInChildren<Renderer>();
                foreach (var renderer in renderers)
                {
                    foreach (var materialOverride in data.materialOverrides)
                    {
                        if (materialOverride.materialSlot < renderer.materials.Length)
                        {
                            var materials = renderer.materials;
                            materials[materialOverride.materialSlot] = materialOverride.material;
                            renderer.materials = materials;
                        }
                    }
                }
            }
        }
        
        private void UpdateObjectTransform(SceneObjectData objectData)
        {
            if (loadedObjects.TryGetValue(objectData.id, out GameObject obj))
            {
                ApplyTransform(obj, objectData);
            }
        }
        
        private void UpdateLighting(LightingSettings lighting)
        {
            if (lighting == null) return;
            
            // Update ambient lighting
            RenderSettings.ambientLight = lighting.ambientColor;
            RenderSettings.ambientIntensity = lighting.ambientIntensity;
            
            // Update directional light (sun)
            var sun = GameObject.FindWithTag("Sun");
            if (sun != null)
            {
                var light = sun.GetComponent<Light>();
                if (light != null)
                {
                    light.color = lighting.sunColor;
                    light.intensity = lighting.sunIntensity;
                    sun.transform.rotation = Quaternion.Euler(lighting.sunRotation);
                }
            }
            
            // Update skybox
            if (lighting.skyboxMaterial != null)
            {
                RenderSettings.skybox = lighting.skyboxMaterial;
            }
        }
        
        private void UpdateEnvironment(EnvironmentSettings environment)
        {
            if (environment == null) return;
            
            // Update fog
            RenderSettings.fog = environment.enableFog;
            if (environment.enableFog)
            {
                RenderSettings.fogColor = environment.fogColor;
                RenderSettings.fogMode = environment.fogMode;
                RenderSettings.fogStartDistance = environment.fogStart;
                RenderSettings.fogEndDistance = environment.fogEnd;
            }
            
            // Update wind
            if (environment.windZone != null)
            {
                var windZone = FindObjectOfType<WindZone>();
                if (windZone != null)
                {
                    windZone.windMain = environment.windStrength;
                    windZone.windTurbulence = environment.windTurbulence;
                }
            }
        }
        
        private void UpdateLODAndCulling()
        {
            if (occlusionCamera == null) return;
            
            // Update camera frustum
            GeometryUtility.CalculateFrustumPlanes(occlusionCamera, cameraFrustum);
            
            Vector3 cameraPos = occlusionCamera.transform.position;
            
            foreach (var obj in activeObjects.ToArray())
            {
                if (obj == null)
                {
                    activeObjects.Remove(obj);
                    continue;
                }
                
                float distance = Vector3.Distance(cameraPos, obj.transform.position);
                
                // Distance culling
                bool shouldBeVisible = distance <= cullingDistance;
                
                // Frustum culling
                if (shouldBeVisible)
                {
                    var bounds = GetObjectBounds(obj);
                    shouldBeVisible = GeometryUtility.TestPlanesAABB(cameraFrustum, bounds);
                }
                
                // Update visibility
                if (obj.activeSelf != shouldBeVisible)
                {
                    obj.SetActive(shouldBeVisible);
                }
                
                // Update LOD
                if (shouldBeVisible && lodGroups.ContainsKey(obj))
                {
                    UpdateObjectLOD(obj, distance);
                }
            }
        }
        
        private Bounds GetObjectBounds(GameObject obj)
        {
            var renderers = obj.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0)
                return new Bounds(obj.transform.position, Vector3.one);
            
            var bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
            {
                bounds.Encapsulate(renderers[i].bounds);
            }
            
            return bounds;
        }
        
        private void UpdateObjectLOD(GameObject obj, float distance)
        {
            if (!lodGroups.TryGetValue(obj, out LODGroup lodGroup))
                return;
            
            // Force LOD update based on distance
            float lodValue = Mathf.Clamp01(1f - (distance / cullingDistance));
            lodGroup.ForceLOD(GetLODLevel(distance));
        }
        
        private int GetLODLevel(float distance)
        {
            if (distance <= lodDistance1) return 0;
            if (distance <= lodDistance2) return 1;
            return 2;
        }
        
        public void ClearScene()
        {
            ClearAllObjects();
        }
        
        private void ClearNonPersistentObjects()
        {
            var objectsToRemove = new List<string>();
            
            foreach (var kvp in loadedObjects)
            {
                var obj = kvp.Value;
                if (obj != null && !obj.CompareTag("Persistent"))
                {
                    objectsToRemove.Add(kvp.Key);
                    activeObjects.Remove(obj);
                    lodGroups.Remove(obj);
                    Destroy(obj);
                }
            }
            
            foreach (var id in objectsToRemove)
            {
                loadedObjects.Remove(id);
            }
        }
        
        private void ClearAllObjects()
        {
            foreach (var kvp in loadedObjects)
            {
                if (kvp.Value != null)
                {
                    Destroy(kvp.Value);
                }
            }
            
            loadedObjects.Clear();
            activeObjects.Clear();
            lodGroups.Clear();
            
            // Cancel any pending loads
            foreach (var handle in loadingOperations.Values)
            {
                if (handle.IsValid())
                {
                    Addressables.Release(handle);
                }
            }
            loadingOperations.Clear();
        }
        
        private void OnDestroy()
        {
            ClearAllObjects();
        }
    }
    
    [System.Serializable]
    public class SceneLoadRequest
    {
        public SceneObjectData objectData;
        public int priority;
    }
}
