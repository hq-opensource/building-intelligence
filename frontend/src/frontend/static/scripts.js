// File: scripts.js

const translations = {
    en: {
        saveSuccess: "Save successful",
        saveError: "Save failed",
        coordinator: {
            title: "Power limit control",
            applyButton: "Apply Power Limit",
            stopButton: "Stop Power Limit",
            placeholder: "Enter power limit",
            saveSuccess: "Power limit of {powerLimit} kW successfully applied",
            saveError: "An error occurred while applying the power limit."
        },
        priorities: {
            title: "Device Priorities",
            editDevice: "Edit device",
            highPriority: "High Priority",
            mediumPriority: "Medium Priority",
            lowPriority: "Low Priority",
            save: "Save",
            cancel: "Cancel",
            editPropertiesTitle: "Edit Device",
            saveSuccess: "Priorities updated successfully!",
            saveError: "Error updating priorities",
        },
        mpc: {
            title: "Model Predictive Contro (MPC)",
            applyButton: "Appliquer la limite de puissance",
            stopButton: "Arrêter la limite de puissance",
            placeholder: "Entrez la limite de puissance",
            saveSuccess: "Limite de puissance de {powerLimit} kW appliquée avec succès",
            saveError: "Une erreur est survenue lors de l'application de la limite de puissance"
        },
        index: {
            title: "Home Energy Management System",
            priority: "Device Prioritization",
            management: "Power Management",
        },
        friendlyNames: {
            water_heater: "Water Heater",
            ev_switch: "EV charger",
            battery: "Electric Battery",
            kitchen: "Thermostat - Kitchen",
            dining_room: "Thermostat - Dining Room",
            sensor_battery: "Battery",
            bathroom: "Thermostat - Bathroom",
            garage: "Thermostat - Garage",
            bedroom_1: "Thermostat - Bedroom 1",
            bedroom_2: "Thermostat - Bedroom 2",
            bedroom_3: "Thermostat - Bedroom 3",
            living_room: "Thermostat - Living Room",
            basement_1: "Thermostat - Basement 1",
            basement_2: "Thermostat - Basement 2",
        },
        deviceProperties: {
            entity_id: "ID",
            friendly_name: "Name",
            activation_action: "Activation action",
            deactivation_action: "Deactivation action",
        },
    },
    fr: {
        saveSuccess: "Enregistrement réussi",
        saveError: "Échec de l'enregistrement",
        coordinator: {
            title: "Contrôle de la limite de puissance",
            applyButton: "Appliquer la limite de puissance",
            stopButton: "Arrêter la limite de puissance",
            placeholder: "Entrez la limite de puissance",
            saveSuccess: "Limite de puissance de {powerLimit} kW appliquée avec succès",
            saveError: "Une erreur est survenue lors de l'application de la limite de puissance"
        },
        priorities: {
            title: "Priorités des Appareils",
            editDevice: "Modifier l'appareil",
            highPriority: "Haute Priorité",
            mediumPriority: "Priorité Moyenne",
            lowPriority: "Basse Priorité",
            save: "Enregistrer",
            cancel: "Annuler",
            editPropertiesTitle: "Modifier l'appareil",
            saveSuccess: "Priorités mises à jour avec succès!",
            saveError: "Erreur lors de la mise à jour des priorités",
        },
        mpc: {
            title: "Contrôle Prédictif par Modèle (MPC)",
            applyButton: "Appliquer la limite de puissance",
            stopButton: "Arrêter la limite de puissance",
            placeholder: "Entrez la limite de puissance",
            saveSuccess: "Limite de puissance de {powerLimit} kW appliquée avec succès",
            saveError: "Une erreur est survenue lors de l'application de la limite de puissance"
        },
        index: {
            title: "Système de gestion énergétique résidentiel",
            priority: "Priorités des appareils",
            management: "Gestion de la puissance",
        },
        friendlyNames: {
            water_heater: "Chauffe-eau",
            ev_switch: "Borne de recharge pour VE",
            battery: "Batterie Électrique",
            kitchen: "Thermostat - Cuisine",
            dining_room: "Thermostat - Salle à Manger",
            sensor_battery: "Batterie",
            bathroom: "Thermostat - Salle de Bain",
            garage: "Thermostat - Garage",
            bedroom_1: "Thermostat - Chambre 1",
            bedroom_2: "Thermostat - Chambre 2",
            bedroom_3: "Thermostat - Chambre 3",
            living_room: "Thermostat - Salon",
            basement_1: "Thermostat - Sous-sol 1",
            basement_2: "Thermostat - Sous-sol 2",
        },
        deviceProperties: {
            entity_id: "ID",
            friendly_name: "Nom",
            activation_action: "Seuil supérieur",
            deactivation_action: "Seuil inférieur",
        },
    },
};

// Gestionnaire de langue
const LanguageManager = {
    // Langue par défaut
    defaultLanguage: 'fr',

    // Obtenir la langue actuelle
    getCurrentLanguage() {
        return localStorage.getItem('selectedLanguage') || this.defaultLanguage;
    },

    // Définir la langue
    setLanguage(lang) {
        if (!translations[lang]) {
            console.warn(`Langue "${lang}" non supportée`);
            return;
        }

        localStorage.setItem('selectedLanguage', lang);
        this.applyTranslations();

        // Émettre un événement pour informer l'application du changement de langue
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
    },

    // Appliquer les traductions
    applyTranslations() {
        const currentLang = this.getCurrentLanguage();
        const page = document.body.dataset.page;
        const pageTranslations = translations[currentLang]?.[page];

        if (!pageTranslations) return;

        document.querySelectorAll('[data-translate-key]').forEach(element => {
            const key = element.dataset.translateKey;
            if (pageTranslations[key]) {
                if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
                    element.placeholder = pageTranslations[key];
                } else {
                    element.textContent = pageTranslations[key];
                }
            }
        });
    },

    // Initialisation
    init() {
        // Appliquer les traductions au chargement
        this.applyTranslations();

        // Ajouter les écouteurs pour les boutons de changement de langue
        document.querySelectorAll('[data-language]').forEach(button => {
            button.addEventListener('click', (e) => {
                const lang = e.target.dataset.language;
                this.setLanguage(lang);
            });
        });
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    LanguageManager.init();
});

// Réappliquer les traductions lors de la navigation avec AJAX (si applicable)
document.addEventListener('pageLoaded', () => {
    LanguageManager.applyTranslations();
});