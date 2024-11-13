using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using Newtonsoft.Json;

class Program
{
    // Define the output directory for ready mods
    static string READY_FOLDER = "ready";

    static void Main(string[] args)
    {
        // Check if any file arguments are passed
        List<string> jarFiles = new List<string>();
        if (args.Length == 0)
        {
            string[] files = Directory.GetFiles(Directory.GetCurrentDirectory(), "*.jar");
            if (files.Length > 0)
            {
                Console.WriteLine("No JAR files provided. Detected the following JAR files in the current directory:");
                foreach (var file in files)
                {
                    Console.WriteLine($"  - {file}");
                }

                Console.Write("Would you like to patch all detected JAR files? (y/n): ");
                if (Console.ReadLine().ToLower() != "y")
                {
                    Console.WriteLine("No files selected. Exiting...");
                    return;
                }
                jarFiles.AddRange(files);
            }
            else
            {
                Console.WriteLine("No JAR files found in the current directory.");
                return;
            }
        }
        else
        {
            jarFiles.AddRange(args);
        }

        // Prompt for Minecraft version
        string defaultVersion = "1.21.3";
        Console.Write($"Enter the target Minecraft version (or press Enter for default {defaultVersion}): ");
        string targetVersion = Console.ReadLine();
        if (string.IsNullOrEmpty(targetVersion))
        {
            targetVersion = defaultVersion;
        }

        Console.WriteLine($"\nTarget Minecraft version set to {targetVersion}.\n");

        // Create the "ready" folder if it doesn't exist
        if (!Directory.Exists(READY_FOLDER))
        {
            Directory.CreateDirectory(READY_FOLDER);
        }

        // Process each jar file
        foreach (var jarFile in jarFiles)
        {
            Console.WriteLine($"Processing file: {Path.GetFileName(jarFile)}");

            try
            {
                string result = PatchFabricMod(jarFile, targetVersion);
                Console.WriteLine(result);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error processing {jarFile}: {ex.Message}");
            }
        }

        Console.WriteLine("\nAll processed mods are available in the 'ready' directory.");
        Console.WriteLine("Press any key to exit...");
        Console.ReadKey();
    }

    static string PatchFabricMod(string jarPath, string targetMinecraftVersion)
    {
        string extractDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        string modJsonPath = Path.Combine(extractDir, "fabric.mod.json");

        // Extract the JAR file
        using (ZipArchive archive = ZipFile.OpenRead(jarPath))
        {
            archive.ExtractToDirectory(extractDir);
        }

        // Check if the mod file contains a fabric.mod.json
        if (!File.Exists(modJsonPath))
        {
            return $"Error: fabric.mod.json not found in {jarPath}.";
        }

        // Read and modify the JSON file
        dynamic modData = JsonConvert.DeserializeObject(File.ReadAllText(modJsonPath));

        if (modData.depends?.minecraft == null)
        {
            return $"Already compatible: {jarPath} (no Minecraft version dependency)";
        }

        modData.depends.minecraft = targetMinecraftVersion;

        // Modify the name to add [PATCHED]
        if (modData.name != null && !modData.name.StartsWith("[PATCHED]"))
        {
            modData.name = "[PATCHED] " + modData.name;
        }

        // Save the modified JSON
        File.WriteAllText(modJsonPath, JsonConvert.SerializeObject(modData, Formatting.Indented));

        // Create the patched JAR file
        string patchedJarPath = Path.Combine(READY_FOLDER, $"_patched_{Path.GetFileName(jarPath)}");
        using (ZipArchive patchedJar = ZipFile.Open(patchedJarPath, ZipArchiveMode.Create))
        {
            foreach (var file in Directory.GetFiles(extractDir, "*", SearchOption.AllDirectories))
            {
                string relativePath = Path.GetRelativePath(extractDir, file);
                patchedJar.CreateEntryFromFile(file, relativePath);
            }
        }

        return $"Patched mod saved as {patchedJarPath}";
    }
}
