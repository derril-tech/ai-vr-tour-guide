import { Injectable, Logger } from '@nestjs/common';
import { SubtitleService } from './subtitle.service';
import { FontService } from './font.service';
import { HandTrackingService } from './hand-tracking.service';
import { ContrastService } from './contrast.service';

interface AccessibilityProfile {
  userId: string;
  visualImpairment: {
    enabled: boolean;
    level: 'mild' | 'moderate' | 'severe' | 'blind';
    preferences: {
      highContrast: boolean;
      largeText: boolean;
      screenReader: boolean;
      audioDescriptions: boolean;
      tactileFeedback: boolean;
    };
  };
  hearingImpairment: {
    enabled: boolean;
    level: 'mild' | 'moderate' | 'severe' | 'deaf';
    preferences: {
      subtitles: boolean;
      signLanguage: boolean;
      visualCues: boolean;
      hapticFeedback: boolean;
      amplification: boolean;
    };
  };
  motorImpairment: {
    enabled: boolean;
    level: 'mild' | 'moderate' | 'severe';
    preferences: {
      handTracking: boolean;
      eyeTracking: boolean;
      voiceControl: boolean;
      simplifiedControls: boolean;
      dwellTime: number;
    };
  };
  cognitiveSupport: {
    enabled: boolean;
    preferences: {
      simplifiedLanguage: boolean;
      clearNavigation: boolean;
      progressIndicators: boolean;
      repetition: boolean;
      pauseOptions: boolean;
    };
  };
  dyslexiaSupport: {
    enabled: boolean;
    preferences: {
      dyslexiaFriendlyFont: boolean;
      increasedSpacing: boolean;
      colorOverlays: boolean;
      readingGuides: boolean;
      audioSupport: boolean;
    };
  };
}

@Injectable()
export class AccessibilityService {
  private readonly logger = new Logger(AccessibilityService.name);

  constructor(
    private subtitleService: SubtitleService,
    private fontService: FontService,
    private handTrackingService: HandTrackingService,
    private contrastService: ContrastService,
  ) {}

  /**
   * Create accessibility profile for user
   */
  async createAccessibilityProfile(userId: string, needs: string[]): Promise<AccessibilityProfile> {
    const profile: AccessibilityProfile = {
      userId,
      visualImpairment: {
        enabled: needs.includes('visual_impairment'),
        level: this.determineVisualImpairmentLevel(needs),
        preferences: {
          highContrast: needs.includes('high_contrast'),
          largeText: needs.includes('large_text'),
          screenReader: needs.includes('screen_reader'),
          audioDescriptions: needs.includes('audio_descriptions'),
          tactileFeedback: needs.includes('tactile_feedback'),
        },
      },
      hearingImpairment: {
        enabled: needs.includes('hearing_impairment'),
        level: this.determineHearingImpairmentLevel(needs),
        preferences: {
          subtitles: needs.includes('subtitles'),
          signLanguage: needs.includes('sign_language'),
          visualCues: needs.includes('visual_cues'),
          hapticFeedback: needs.includes('haptic_feedback'),
          amplification: needs.includes('amplification'),
        },
      },
      motorImpairment: {
        enabled: needs.includes('motor_impairment'),
        level: this.determineMotorImpairmentLevel(needs),
        preferences: {
          handTracking: needs.includes('hand_tracking'),
          eyeTracking: needs.includes('eye_tracking'),
          voiceControl: needs.includes('voice_control'),
          simplifiedControls: needs.includes('simplified_controls'),
          dwellTime: this.calculateDwellTime(needs),
        },
      },
      cognitiveSupport: {
        enabled: needs.includes('cognitive_support'),
        preferences: {
          simplifiedLanguage: needs.includes('simplified_language'),
          clearNavigation: needs.includes('clear_navigation'),
          progressIndicators: needs.includes('progress_indicators'),
          repetition: needs.includes('repetition'),
          pauseOptions: needs.includes('pause_options'),
        },
      },
      dyslexiaSupport: {
        enabled: needs.includes('dyslexia_support'),
        preferences: {
          dyslexiaFriendlyFont: needs.includes('dyslexia_font'),
          increasedSpacing: needs.includes('increased_spacing'),
          colorOverlays: needs.includes('color_overlays'),
          readingGuides: needs.includes('reading_guides'),
          audioSupport: needs.includes('audio_support'),
        },
      },
    };

    this.logger.log(`Created accessibility profile for user ${userId}`);
    return profile;
  }

  /**
   * Generate accessibility adaptations for content
   */
  async generateAccessibilityAdaptations(
    content: any,
    profile: AccessibilityProfile
  ): Promise<any> {
    const adaptations: any = {
      original: content,
      adaptations: {},
    };

    // Visual impairment adaptations
    if (profile.visualImpairment.enabled) {
      adaptations.adaptations.visual = await this.generateVisualAdaptations(content, profile.visualImpairment);
    }

    // Hearing impairment adaptations
    if (profile.hearingImpairment.enabled) {
      adaptations.adaptations.hearing = await this.generateHearingAdaptations(content, profile.hearingImpairment);
    }

    // Motor impairment adaptations
    if (profile.motorImpairment.enabled) {
      adaptations.adaptations.motor = await this.generateMotorAdaptations(content, profile.motorImpairment);
    }

    // Cognitive support adaptations
    if (profile.cognitiveSupport.enabled) {
      adaptations.adaptations.cognitive = await this.generateCognitiveAdaptations(content, profile.cognitiveSupport);
    }

    // Dyslexia support adaptations
    if (profile.dyslexiaSupport.enabled) {
      adaptations.adaptations.dyslexia = await this.generateDyslexiaAdaptations(content, profile.dyslexiaSupport);
    }

    return adaptations;
  }

  /**
   * Generate visual accessibility adaptations
   */
  private async generateVisualAdaptations(content: any, visualProfile: any): Promise<any> {
    const adaptations: any = {};

    if (visualProfile.preferences.highContrast) {
      adaptations.highContrast = await this.contrastService.generateHighContrastVersion(content);
    }

    if (visualProfile.preferences.largeText) {
      adaptations.largeText = await this.fontService.generateLargeTextVersion(content);
    }

    if (visualProfile.preferences.audioDescriptions) {
      adaptations.audioDescriptions = await this.generateAudioDescriptions(content);
    }

    if (visualProfile.preferences.tactileFeedback) {
      adaptations.tactileFeedback = await this.generateTactileFeedback(content);
    }

    return adaptations;
  }

  /**
   * Generate hearing accessibility adaptations
   */
  private async generateHearingAdaptations(content: any, hearingProfile: any): Promise<any> {
    const adaptations: any = {};

    if (hearingProfile.preferences.subtitles) {
      adaptations.subtitles = await this.subtitleService.generateSubtitles(content);
    }

    if (hearingProfile.preferences.signLanguage) {
      adaptations.signLanguage = await this.generateSignLanguageInterpretation(content);
    }

    if (hearingProfile.preferences.visualCues) {
      adaptations.visualCues = await this.generateVisualCues(content);
    }

    if (hearingProfile.preferences.hapticFeedback) {
      adaptations.hapticFeedback = await this.generateHapticPatterns(content);
    }

    return adaptations;
  }

  /**
   * Generate motor accessibility adaptations
   */
  private async generateMotorAdaptations(content: any, motorProfile: any): Promise<any> {
    const adaptations: any = {};

    if (motorProfile.preferences.handTracking) {
      adaptations.handTracking = await this.handTrackingService.generateHandTrackingControls(content);
    }

    if (motorProfile.preferences.voiceControl) {
      adaptations.voiceControl = await this.generateVoiceControlCommands(content);
    }

    if (motorProfile.preferences.simplifiedControls) {
      adaptations.simplifiedControls = await this.generateSimplifiedControls(content);
    }

    adaptations.dwellTime = motorProfile.preferences.dwellTime;

    return adaptations;
  }

  /**
   * Generate cognitive support adaptations
   */
  private async generateCognitiveAdaptations(content: any, cognitiveProfile: any): Promise<any> {
    const adaptations: any = {};

    if (cognitiveProfile.preferences.simplifiedLanguage) {
      adaptations.simplifiedLanguage = await this.generateSimplifiedLanguage(content);
    }

    if (cognitiveProfile.preferences.clearNavigation) {
      adaptations.clearNavigation = await this.generateClearNavigation(content);
    }

    if (cognitiveProfile.preferences.progressIndicators) {
      adaptations.progressIndicators = await this.generateProgressIndicators(content);
    }

    return adaptations;
  }

  /**
   * Generate dyslexia support adaptations
   */
  private async generateDyslexiaAdaptations(content: any, dyslexiaProfile: any): Promise<any> {
    const adaptations: any = {};

    if (dyslexiaProfile.preferences.dyslexiaFriendlyFont) {
      adaptations.dyslexiaFont = await this.fontService.generateDyslexiaFriendlyVersion(content);
    }

    if (dyslexiaProfile.preferences.increasedSpacing) {
      adaptations.increasedSpacing = await this.fontService.generateIncreasedSpacing(content);
    }

    if (dyslexiaProfile.preferences.colorOverlays) {
      adaptations.colorOverlays = await this.generateColorOverlays(content);
    }

    if (dyslexiaProfile.preferences.readingGuides) {
      adaptations.readingGuides = await this.generateReadingGuides(content);
    }

    return adaptations;
  }

  // Helper methods for generating specific adaptations

  private async generateAudioDescriptions(content: any): Promise<any> {
    return {
      descriptions: [
        "Visual scene description available",
        "Spatial audio cues enabled",
        "Object identification active"
      ],
      spatialAudio: true,
      objectIdentification: true,
    };
  }

  private async generateTactileFeedback(content: any): Promise<any> {
    return {
      patterns: {
        navigation: "short_pulse",
        interaction: "double_pulse",
        confirmation: "long_pulse",
        warning: "rapid_pulse",
      },
      intensity: "medium",
    };
  }

  private async generateSignLanguageInterpretation(content: any): Promise<any> {
    return {
      avatarEnabled: true,
      language: "ASL",
      position: "bottom_right",
      size: "medium",
    };
  }

  private async generateVisualCues(content: any): Promise<any> {
    return {
      soundVisualization: true,
      flashingIndicators: true,
      colorCodedAlerts: true,
      vibrationPatterns: {
        notification: [100, 50, 100],
        alert: [200, 100, 200, 100, 200],
        confirmation: [300],
      },
    };
  }

  private async generateHapticPatterns(content: any): Promise<any> {
    return {
      audioReplacementPatterns: {
        speech: "gentle_rhythm",
        music: "flowing_pattern",
        effects: "sharp_bursts",
      },
      intensityLevels: ["low", "medium", "high"],
    };
  }

  private async generateVoiceControlCommands(content: any): Promise<any> {
    return {
      commands: {
        navigation: ["go forward", "go back", "look up", "look down"],
        interaction: ["select", "activate", "cancel", "help"],
        content: ["play", "pause", "repeat", "skip"],
      },
      wakeWord: "tour guide",
      confidence: 0.8,
    };
  }

  private async generateSimplifiedControls(content: any): Promise<any> {
    return {
      reducedButtons: true,
      largerTargets: true,
      gestureAlternatives: true,
      dwellSelection: true,
      confirmationDialogs: true,
    };
  }

  private async generateSimplifiedLanguage(content: any): Promise<any> {
    return {
      vocabularyLevel: "elementary",
      sentenceLength: "short",
      conceptExplanations: true,
      visualAids: true,
    };
  }

  private async generateClearNavigation(content: any): Promise<any> {
    return {
      breadcrumbs: true,
      stepIndicators: true,
      clearLabels: true,
      consistentLayout: true,
      skipLinks: true,
    };
  }

  private async generateProgressIndicators(content: any): Promise<any> {
    return {
      completionPercentage: true,
      timeRemaining: true,
      stepCounter: true,
      visualProgress: true,
    };
  }

  private async generateColorOverlays(content: any): Promise<any> {
    return {
      overlayColors: ["blue", "yellow", "pink", "green"],
      opacity: 0.2,
      userSelectable: true,
    };
  }

  private async generateReadingGuides(content: any): Promise<any> {
    return {
      lineHighlight: true,
      wordHighlight: true,
      readingRuler: true,
      focusMode: true,
    };
  }

  // Helper methods for determining impairment levels

  private determineVisualImpairmentLevel(needs: string[]): 'mild' | 'moderate' | 'severe' | 'blind' {
    if (needs.includes('blind')) return 'blind';
    if (needs.includes('severe_visual')) return 'severe';
    if (needs.includes('moderate_visual')) return 'moderate';
    return 'mild';
  }

  private determineHearingImpairmentLevel(needs: string[]): 'mild' | 'moderate' | 'severe' | 'deaf' {
    if (needs.includes('deaf')) return 'deaf';
    if (needs.includes('severe_hearing')) return 'severe';
    if (needs.includes('moderate_hearing')) return 'moderate';
    return 'mild';
  }

  private determineMotorImpairmentLevel(needs: string[]): 'mild' | 'moderate' | 'severe' {
    if (needs.includes('severe_motor')) return 'severe';
    if (needs.includes('moderate_motor')) return 'moderate';
    return 'mild';
  }

  private calculateDwellTime(needs: string[]): number {
    if (needs.includes('severe_motor')) return 2000; // 2 seconds
    if (needs.includes('moderate_motor')) return 1500; // 1.5 seconds
    return 1000; // 1 second
  }
}
