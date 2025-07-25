import json
from datetime import datetime

class UrbanInsightsAnalyser:
    def analysis(self, results):
        insights = []
        insights.append("CITY OF LONDON BUILDING ANALYSIS")
        insights.append("=" * 60)
        
        # Basic overview
        if 'basic_stats' in results and not results['basic_stats'].empty:
            stats = results['basic_stats'].iloc[0]
            insights.append(f"\nDATASET OVERVIEW:")
            insights.append(f"   • Total Number of Buildings Analysed: {stats['total_buildings']:,}")
            insights.append(f"   • Average Building Height: {stats['avg_height_m']} m")
            insights.append(f"   • Tallest Building: {stats['max_height_m']} m")
            insights.append(f"   • Average Building Volume: {stats['avg_volume_m3']:,.0f} m^3")
            insights.append(f"   • Number of Building Types: {stats['building_types']} types")
            insights.append("\n" + "=" * 60)
        
        # Height distribution
        if 'height_distribution' in results and not results['height_distribution'].empty:
            insights.append(f"\nHEIGHT DISTRIBUTION:")
            for _, row in results['height_distribution'].iterrows():
                category = row['height_category'].replace('_', '-').title()
                insights.append(f"   • {category}: {row['building_count']} buildings ({row['percentage']}%)")
                insights.append(f"     - Average height: {row['avg_height']}m")
        
        # Building type
        if 'building_types' in results and not results['building_types'].empty:
            insights.append(f"\nBUILDING TYPE ANALYSIS:")
            for _, row in results['building_types'].iterrows():
                building_type = row['building_type'].title()
                insights.append(f"   • {building_type}: {row['count']} buildings")
                insights.append(f"     - Average height: {row['avg_height']}m")
                insights.append(f"     - Average footprint: {row['avg_footprint_m2']:,.0f} m²")
            insights.append("\n" + "=" * 60)

        # Spatial clustering
        if 'spatial_clusters' in results and not results['spatial_clusters'].empty:
            clusters = results['spatial_clusters']
            insights.append(f"\nSPATIAL CLUSTERING ANALYSIS:")
            insights.append(f"   • {len(clusters)} high-rise clusters identified (with PostGIS DBSCAN)")
            insights.append(f"   • Clusters contain buildings >40m height within 200m radius")
            
            if len(clusters) > 0:
                # Largest cluster
                biggest = clusters.iloc[0]
                insights.append(f"\nLARGEST CLUSTER:")
                insights.append(f"     - Buildings in cluster: {biggest['buildings_in_cluster']}")
                insights.append(f"     - Average cluster height: {biggest['avg_cluster_height']}m")
                insights.append(f"     - Tallest building: {biggest['tallest_in_cluster']}m")
                
                # Print all clusters
                insights.append(f"\nALL CLUSTERS:")
                for idx, row in clusters.iterrows():
                    # Clean string (remove group 'yes' category)
                    types = ', '.join(t for t in row['building_types'].split(', ') if t.lower() != 'yes')
                    insights.append(
                        f"   • Cluster {row['cluster_id'] + 1}: "
                        f"{row['buildings_in_cluster']} buildings, "
                        f"avg height {row['avg_cluster_height']}m, "
                        f"tallest {row['tallest_in_cluster']}m, "
                        f"types: {types if types else 'unknown'}"
                    )

                # Cluster summary
                total_clustered = clusters['buildings_in_cluster'].sum()
                insights.append(f"\nCLUSTER SUMMARY:")
                insights.append(f"     - Total buildings in clusters: {total_clustered}")
                insights.append(f"     - Average cluster size: {clusters['buildings_in_cluster'].mean():.1f} buildings")
        else:
            insights.append(f"\nSPATIAL CLUSTERING ANALYSIS:")
            insights.append(f"   • No significant clusters detected, hence buildings are relatively dispersed")
        
        insights_text = '\n'.join(insights)
        
        # Save to file
        with open('london_urban_insights.txt', 'w', encoding='utf-8') as f:
            f.write(insights_text)
                
        return insights_text

    def save_analysis_summary(self, results, runtime):
        summary = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'runtime_seconds': round(runtime, 2),
                'analysis_type': 'london_buildings_spatial_analysis'
            },
            'dataset_stats': {},
            'analysis_results': {}
        }
        
        # DataFrames to dictionary
        for key, df in results.items():
            if hasattr(df, 'to_dict'):
                summary['analysis_results'][key] = df.to_dict('records')
            else:
                summary['analysis_results'][key] = str(df)
        
        # Extract key stats
        if 'basic_stats' in results and not results['basic_stats'].empty:
            stats = results['basic_stats'].iloc[0]
            summary['dataset_stats'] = {
                'total_buildings': int(stats['total_buildings']),
                'avg_height_m': float(stats['avg_height_m']),
                'max_height_m': float(stats['max_height_m']),
                'avg_volume_m3': float(stats['avg_volume_m3']),
                'building_types': int(stats['building_types'])
            }
        
        # Save to file
        with open('analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return summary
