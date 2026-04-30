import React, { useState } from 'react';
import { StyleSheet, Text, View, Button, Image, ScrollView, ActivityIndicator, TextInput, Alert, TouchableOpacity } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import axios from 'axios';

export default function App() {
  const [imageUri, setImageUri] = useState(null);
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState('http://192.168.1.100:8000/api/v1/analyze'); // Replace with actual local IP

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.8,
    });
    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
      setDishes([]);
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Sorry, we need camera permissions to make this work!');
      return;
    }
    let result = await ImagePicker.launchCameraAsync({
      allowsEditing: false,
      quality: 0.8,
    });
    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
      setDishes([]);
    }
  };

  const analyzeMenu = async () => {
    if (!imageUri) return;
    setLoading(true);
    setDishes([]);

    let localUri = imageUri;
    let filename = localUri.split('/').pop() || 'menu.jpg';
    let match = /\.(\w+)$/.exec(filename);
    let type = match ? `image/${match[1]}` : `image/jpeg`;

    let formData = new FormData();
    formData.append('file', { uri: localUri, name: filename, type });

    try {
      const response = await axios.post(apiUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 45000,
      });
      if (response.data && response.data.dishes) {
        setDishes(response.data.dishes);
      } else {
        Alert.alert('Error', 'Unexpected response format from server.');
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Error', error.response?.data?.detail || error.message || 'Failed to connect to backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>🍽️ MenuMate MVP</Text>
      <Text style={styles.subtitle}>Don't just translate — visualize.</Text>
      
      <View style={styles.configContainer}>
        <Text style={styles.label}>Backend URL (Change to your Local IP):</Text>
        <TextInput
          style={styles.input}
          value={apiUrl}
          onChangeText={setApiUrl}
          autoCapitalize="none"
        />
      </View>

      <View style={styles.buttonRow}>
        <Button title="📸 Take Photo" onPress={takePhoto} />
        <Button title="📂 Pick Image" onPress={pickImage} />
      </View>

      {imageUri && (
        <View style={styles.imageContainer}>
          <Image source={{ uri: imageUri }} style={styles.image} />
          <View style={{ marginTop: 10 }}>
            <Button title="✨ Analyze Menu" onPress={analyzeMenu} color="#ea580c" />
          </View>
        </View>
      )}

      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#ea580c" />
          <Text style={{ marginTop: 10 }}>👨‍🍳 Reading the menu — this takes ~10 seconds…</Text>
        </View>
      )}

      {dishes.length > 0 && (
        <View style={styles.resultsContainer}>
          <Text style={styles.sectionTitle}>📋 Detected Dishes</Text>
          {dishes.map((dish, index) => (
            <View key={index} style={styles.card}>
              <Text style={styles.dishTranslated}>{dish.translated_name}</Text>
              <Text style={styles.dishOriginal}>{dish.original_name}</Text>
              {dish.pronunciation_guide ? <Text style={styles.dishPronunciation}>🗣 {dish.pronunciation_guide}</Text> : null}
              {dish.price ? <Text style={styles.dishPrice}>{dish.price}</Text> : null}
              
              <Text style={styles.dishDesc}>{dish.description}</Text>
              
              {dish.main_ingredients && dish.main_ingredients.length > 0 && (
                <Text style={styles.dishIngredients}>🧂 {dish.main_ingredients.join(', ')}</Text>
              )}
              
              <View style={styles.tagContainer}>
                {dish.taste_tags && dish.taste_tags.map((tag, idx) => (
                  <Text key={idx} style={styles.tag}>{tag}</Text>
                ))}
              </View>
              
              {dish.calories_estimate ? <Text style={styles.dishCalories}>~{dish.calories_estimate}</Text> : null}
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
    backgroundColor: '#fafaf9',
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1c1917',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#78716c',
    textAlign: 'center',
    marginBottom: 20,
  },
  configContainer: {
    marginBottom: 20,
    padding: 10,
    backgroundColor: '#fff',
    borderRadius: 8,
  },
  label: {
    fontSize: 12,
    color: '#44403c',
    marginBottom: 5,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e7e5e4',
    padding: 8,
    borderRadius: 4,
    fontSize: 14,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  imageContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  image: {
    width: 300,
    height: 400,
    resizeMode: 'contain',
    borderRadius: 10,
  },
  loadingContainer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  resultsContainer: {
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1c1917',
    marginBottom: 15,
    borderBottomWidth: 2,
    borderBottomColor: '#ea580c',
    paddingBottom: 5,
  },
  card: {
    backgroundColor: '#ffffff',
    padding: 15,
    borderRadius: 12,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#e7e5e4',
    elevation: 2,
  },
  dishTranslated: {
    fontSize: 14,
    color: '#ea580c',
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  dishOriginal: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1c1917',
    marginTop: 4,
  },
  dishPronunciation: {
    fontSize: 13,
    color: '#78716c',
    fontStyle: 'italic',
    marginTop: 2,
  },
  dishPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    position: 'absolute',
    top: 15,
    right: 15,
  },
  dishDesc: {
    fontSize: 15,
    color: '#44403c',
    marginTop: 10,
    lineHeight: 22,
  },
  dishIngredients: {
    fontSize: 13,
    color: '#78716c',
    marginTop: 8,
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 10,
  },
  tag: {
    backgroundColor: '#f5f5f4',
    color: '#57534e',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 15,
    fontSize: 12,
    marginRight: 6,
    marginBottom: 6,
  },
  dishCalories: {
    fontSize: 12,
    color: '#78716c',
    marginTop: 5,
  },
});
